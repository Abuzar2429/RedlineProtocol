"""
Redline-LLM QLoRA Supervised Fine-Tuning (SFT) Script (Phase 2).

Trains an open-weights base LLM (e.g. Qwen 2.5 7B, Llama 3.1 8B, Mistral 7B) on
RedlineProtocol's crisis decision-making, coordinator consensus drafting, and
governance policy datasets using 4-bit QLoRA and Hugging Face TRL.

Usage:
    python training/train_lora.py \
        --base_model "Qwen/Qwen2.5-7B-Instruct" \
        --train_data "training/data/redline_sft_train.jsonl" \
        --val_data "training/data/redline_sft_val.jsonl" \
        --output_dir "models/redline-llm-lora" \
        --epochs 3 \
        --batch_size 2 \
        --grad_accum 4 \
        --lr 2e-4
"""
import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("redline_trainer")


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune Redline-LLM with QLoRA SFT")
    parser.add_argument(
        "--base_model",
        type=str,
        default="Qwen/Qwen2.5-7B-Instruct",
        help="Base model path or HuggingFace repo ID (e.g. Qwen/Qwen2.5-7B-Instruct or meta-llama/Meta-Llama-3.1-8B-Instruct)",
    )
    parser.add_argument(
        "--train_data",
        type=str,
        default="training/data/redline_sft_train.jsonl",
        help="Path to SFT training JSONL",
    )
    parser.add_argument(
        "--val_data",
        type=str,
        default="training/data/redline_sft_val.jsonl",
        help="Path to SFT validation JSONL",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="models/redline-llm-lora",
        help="Directory to save the trained LoRA adapter and checkpoints",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=2, help="Per-device training batch size")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Peak learning rate")
    parser.add_argument("--max_seq_length", type=int, default=2048, help="Maximum sequence length")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank dimension")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA scaling alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout rate")
    parser.add_argument("--use_4bit", action="store_true", default=True, help="Enable 4-bit NF4 QLoRA quantization")
    parser.add_argument("--no_4bit", dest="use_4bit", action="store_false", help="Disable 4-bit quantization (train in 16-bit)")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        import torch
        from datasets import load_dataset
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments,
        )
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from trl import SFTTrainer
    except ImportError as e:
        logger.error(
            f"Required deep learning libraries not found: {e}\n"
            "Please install dependencies with:\n"
            "    pip install -r training/requirements.txt"
        )
        sys.exit(1)

    device_count = torch.cuda.device_count()
    device_name = torch.cuda.get_device_name(0) if device_count > 0 else "CPU"
    logger.info(f"Target Base Model: {args.base_model}")
    logger.info(f"Compute Devices Available: {device_count} ({device_name})")
    logger.info(f"QLoRA 4-bit Quantization: {args.use_4bit}")

    # 1. Load Tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Configure 4-bit Quantization (BitsAndBytes)
    bnb_config = None
    torch_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

    if args.use_4bit and torch.cuda.is_available():
        logger.info("Configuring 4-bit NF4 quantization with double quantization...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch_dtype,
        )

    # 3. Load Model
    logger.info("Loading base causal language model...")
    model_kwargs = {
        "trust_remote_code": True,
        "torch_dtype": torch_dtype,
    }
    if bnb_config is not None:
        model_kwargs["quantization_config"] = bnb_config
        model_kwargs["device_map"] = "auto"
    elif torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)

    # 4. Prepare for k-bit training and LoRA
    if args.use_4bit and torch.cuda.is_available():
        model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

    logger.info("Applying LoRA adapter configuration...")
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 5. Load Datasets
    logger.info(f"Loading training data from {args.train_data}...")
    dataset = load_dataset(
        "json",
        data_files={"train": args.train_data, "validation": args.val_data},
    )

    # Formatting function for ChatML / messages format
    def format_chatml(example):
        messages = example["messages"]
        if hasattr(tokenizer, "apply_chat_template"):
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        else:
            formatted = []
            for msg in messages:
                formatted.append(f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>")
            text = "\n".join(formatted)
        return {"text": text}

    formatted_dataset = dataset.map(format_chatml)

    # 6. Training Arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        bf16=(torch_dtype == torch.bfloat16),
        fp16=(torch_dtype == torch.float16),
        max_grad_norm=0.3,
        weight_decay=0.01,
        report_to="none",
    )

    # 7. SFT Trainer
    logger.info("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=formatted_dataset["train"],
        eval_dataset=formatted_dataset["validation"],
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        tokenizer=tokenizer,
        args=training_args,
    )

    # 8. Run Training
    logger.info("Beginning fine-tuning execution...")
    trainer.train()

    # 9. Save final adapter
    logger.info(f"Saving fine-tuned LoRA adapter to {args.output_dir}...")
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    logger.info("Training successfully finished!")


if __name__ == "__main__":
    main()
