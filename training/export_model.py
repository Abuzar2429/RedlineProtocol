"""
Redline-LLM Adapter Merging & Model Export Utility (Phase 2).

Merges a trained LoRA adapter with the base model to produce a standalone
16-bit SafeTensors model directory, ready for direct inference, vLLM serving,
or conversion to GGUF format for Ollama / llama.cpp.

Usage:
    python training/export_model.py \
        --base_model "Qwen/Qwen2.5-7B-Instruct" \
        --adapter_path "models/redline-llm-lora" \
        --output_dir "models/redline-llm-merged"
"""
import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("redline_exporter")


def parse_args():
    parser = argparse.ArgumentParser(description="Merge LoRA weights and export standalone Redline-LLM")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--adapter_path", type=str, default="models/redline-llm-lora")
    parser.add_argument("--output_dir", type=str, default="models/redline-llm-merged")
    parser.add_argument("--create_modelfile", action="store_true", default=True, help="Generate Ollama Modelfile")
    return parser.parse_args()


def generate_ollama_modelfile(merged_dir: str, target_path: str):
    """
    Creates an Ollama Modelfile tailored for Redline-LLM.
    """
    modelfile_content = f"""# Ollama Modelfile for Redline-LLM (AI Governance Crisis Negotiator)
FROM {merged_dir}

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"

TEMPLATE \"\"\"<|im_start|>system
{{{{ .System }}}}<|im_end|>
<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
\"\"\"

SYSTEM \"\"\"You are the Redline AI Governance Crisis Policy and Negotiation Model.
You analyze international frontier AI incidents, state doctrines, and multilateral accords.
Decisions and proposals must strictly return validated JSON schemas when requested.\"\"\"
"""
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(modelfile_content)
    logger.info(f"Ollama Modelfile written to: {target_path}")


def main():
    args = parse_args()

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as e:
        logger.error(f"Required libraries missing: {e}. Install via `pip install -r training/requirements.txt`")
        sys.exit(1)

    logger.info(f"Loading base model: {args.base_model}...")
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch_dtype,
        device_map="auto" if torch.cuda.is_available() else "cpu",
        trust_remote_code=True,
    )

    logger.info(f"Loading LoRA adapter: {args.adapter_path}...")
    model = PeftModel.from_pretrained(base_model, args.adapter_path)

    logger.info("Merging LoRA weights with base model...")
    merged_model = model.merge_and_unload()

    logger.info(f"Saving merged standalone model to {args.output_dir}...")
    merged_model.save_pretrained(args.output_dir, safe_serialization=True)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.save_pretrained(args.output_dir)

    if args.create_modelfile:
        modelfile_path = Path(args.output_dir) / "Modelfile"
        generate_ollama_modelfile(str(args.output_dir), str(modelfile_path))

    logger.info(f"Model export complete! Model is ready at: {args.output_dir}")


if __name__ == "__main__":
    main()
