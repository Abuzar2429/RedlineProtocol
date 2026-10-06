#!/usr/bin/env bash
# Quick-start script to run Redline-LLM fine-tuning on Google Colab or Linux GPU instance
set -e

echo "=== 1. Installing Training Dependencies ==="
pip install -r training/requirements.txt

echo "=== 2. Regenerating / Verifying Datasets ==="
python training/dataset_generator.py

echo "=== 3. Executing QLoRA Supervised Fine-Tuning (SFT) ==="
python training/train_lora.py \
    --base_model "Qwen/Qwen2.5-7B-Instruct" \
    --train_data "training/data/redline_sft_train.jsonl" \
    --val_data "training/data/redline_sft_val.jsonl" \
    --output_dir "models/redline-llm-lora" \
    --epochs 3 \
    --batch_size 2 \
    --grad_accum 4 \
    --lr 2e-4

echo "=== 4. Executing DPO Preference Alignment ==="
python training/train_dpo.py \
    --base_model "Qwen/Qwen2.5-7B-Instruct" \
    --adapter_path "models/redline-llm-lora" \
    --dpo_data "training/data/redline_dpo_train.jsonl" \
    --output_dir "models/redline-llm-dpo" \
    --epochs 2

echo "=== 5. Merging LoRA Weights into Standalone Model ==="
python training/export_model.py \
    --base_model "Qwen/Qwen2.5-7B-Instruct" \
    --adapter_path "models/redline-llm-dpo" \
    --output_dir "models/redline-llm-final"

echo "=== Training Complete! Model saved to models/redline-llm-final ==="
