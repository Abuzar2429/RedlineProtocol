"""
Redline-LLM Direct Preference Optimization (DPO) Training Script (Phase 2).

Aligns the fine-tuned Redline-LLM using Direct Preference Optimization (DPO)
against the 4-Pillar Scoring Engine (Risk Reduction, Consensus, Timeliness, Liabilities).
Optimizes the policy to prefer diplomatic containment and de-escalation over unilateral
retaliation or information withholding.

Usage:
    python training/train_dpo.py \
        --base_model "Qwen/Qwen2.5-7B-Instruct" \
        --adapter_path "models/redline-llm-lora" \
        --dpo_data "training/data/redline_dpo_train.jsonl" \
        --output_dir "models/redline-llm-dpo" \
        --epochs 2 \
        --beta 0.1 \
        --lr 5e-6
"""
import argparse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("redline_dpo_trainer")


def parse_args():
    parser = argparse.ArgumentParser(description="Align Redline-LLM with DPO")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--adapter_path", type=str, default="models/redline-llm-lora", help="Path to SFT LoRA checkpoint")
    parser.add_argument("--dpo_data", type=str, default="training/data/redline_dpo_train.jsonl")
    parser.add_argument("--output_dir", type=str, default="models/redline-llm-dpo")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--grad_accum", type=int, default=8)
    parser.add_argument("--beta", type=float, default=0.1, help="DPO temperature parameter")
    parser.add_argument("--lr", type=float, default=5e-6)
    parser.add_argument("--max_length", type=int, default=2048)
    parser.add_argument("--max_prompt_length", type=int, default=1024)
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        import torch
        from datasets import load_dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from peft import PeftModel
        from trl import DPOTrainer
    except ImportError as e:
        logger.error(f"Required libraries missing: {e}. Install via `pip install -r training/requirements.txt`")
        sys.exit(1)

    logger.info(f"Loading base tokenizer for {args.base_model}...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    torch_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

    logger.info("Loading model for DPO alignment...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch_dtype,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True,
    )

    if os.path.exists(args.adapter_path):
        logger.info(f"Loading pretrained LoRA adapter from {args.adapter_path}...")
        model = PeftModel.from_pretrained(model, args.adapter_path, is_trainable=True)

    logger.info(f"Loading DPO dataset from {args.dpo_data}...")
    dataset = load_dataset("json", data_files={"train": args.dpo_data})["train"]

    def format_dpo(example):
        system = example.get("system", "")
        prompt = example.get("prompt", "")
        full_prompt = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        return {
            "prompt": full_prompt,
            "chosen": example["chosen"] + "<|im_end|>",
            "rejected": example["rejected"] + "<|im_end|>",
        }

    formatted_dataset = dataset.map(format_dpo)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        logging_steps=5,
        save_strategy="epoch",
        bf16=(torch_dtype == torch.bfloat16),
        fp16=(torch_dtype == torch.float16),
        report_to="none",
    )

    dpo_trainer = DPOTrainer(
        model=model,
        ref_model=None,  # Implicit reference model using PEFT
        beta=args.beta,
        train_dataset=formatted_dataset,
        tokenizer=tokenizer,
        args=training_args,
        max_length=args.max_length,
        max_prompt_length=args.max_prompt_length,
    )

    logger.info("Starting DPO training...")
    dpo_trainer.train()

    logger.info(f"Saving DPO-aligned model to {args.output_dir}...")
    dpo_trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    logger.info("DPO alignment completed successfully!")


if __name__ == "__main__":
    main()
