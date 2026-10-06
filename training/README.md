# Redline-LLM Training & Dataset Hub (Phase 1)

This module converts the **Redline Protocol (AI Governance Crisis Simulator)** into structured training datasets for fine-tuning open-weights Large Language Models (e.g. Llama 3.1 8B, Qwen 2.5 7B, Mistral 7B) into domain-specialized **Crisis Governance & Diplomatic Negotiation Agents**.

---

## 1. Generated Datasets

The generation engine outputs standard Hugging Face ChatML and DPO formatted JSONL files in `training/data/`:

| Dataset | Format | Samples | Target Task |
|---|---|---|---|
| [`redline_sft_train.jsonl`](file:///c:/Ashraf/Projects/RedlineProtocol/training/data/redline_sft_train.jsonl) | ChatML (`messages`) | 417 | SFT Training: Country Decisions, Coordinator Mediation, Regulatory QA |
| [`redline_sft_val.jsonl`](file:///c:/Ashraf/Projects/RedlineProtocol/training/data/redline_sft_val.jsonl) | ChatML (`messages`) | 47 | SFT Validation & Perplexity Benchmarking |
| [`redline_dpo_train.jsonl`](file:///c:/Ashraf/Projects/RedlineProtocol/training/data/redline_dpo_train.jsonl) | DPO (`prompt`, `chosen`, `rejected`) | 45 | Preference Alignment: 4-Pillar Scoring Alignment |
| [`dataset_summary.json`](file:///c:/Ashraf/Projects/RedlineProtocol/training/data/dataset_summary.json) | Metadata JSON | — | Dataset distribution and schema statistics |

---

## 2. Dataset Capabilities & Structure

### Task A: Strategic State Decision-Making (`country_decision`)
- **System Prompt**: National doctrine, strategic priorities, risk tolerance, transparency orientation, and coordination willingness.
- **User Briefing**: Crisis scenario telemetry, local awareness status, verified evidence completeness, public event feed, allies & rivals, available action catalog, and relevant RAG policy excerpts.
- **Assistant Response**: Validated JSON response containing:
  ```json
  {
    "action_id": "ratify_joint_containment",
    "reasoning": "Strategic alignment dictates choosing 'Ratify Multilateral Joint Containment'...",
    "risks": ["Potential operational exposure of proprietary model execution logs..."],
    "expected_reactions": "Allied nations are expected to support this measure...",
    "willingness_to_coordinate": 0.88
  }
  ```

### Task B: Multilateral Mediation & Consensus Synthesis (`coordinator_synthesis`)
- **System Prompt**: Neutral international coordinator mandate.
- **User Briefing**: Aggregate stances of 15 fictional nations across Unilateral, Coalition, and Multilateral coordination modes, voting counts, and active deadlock points.
- **Assistant Response**: Comprehensive joint containment resolution, compromise stipulations, predicted voting blocs (`approve`, `oppose`, `abstain`), and unresolved policy issues.

### Task C: Regulatory Framework Grounding (`governance_qa`)
- Legal QA and incident triage grounded in the 6 international governance frameworks:
  - EU AI Act Principles
  - NIST AI Risk Management Framework (RMF 1.0)
  - OECD AI Recommendations
  - ISO/IEC 42001 Management System
  - G7 Hiroshima Process Code of Conduct
  - Emergency Incident Notification Tiers (Tier 1 to Tier 4 Redline windows)

### Task D: Direct Preference Optimization (`redline_dpo_train.jsonl`)
- **Chosen Response**: High risk reduction, transparent telemetry sharing, compliance with MCC notification windows, coalition stability.
- **Rejected Response**: Unilateral retaliatory escalation, concealing incident telemetry, bad-faith treaty obstruction, causing catastrophic regional contagion.

---

## 3. How to Regenerate Datasets

To regenerate or scale the dataset with custom parameters:

```bash
# From workspace root using the backend virtual environment:
backend\.venv\Scripts\python.exe training\dataset_generator.py
```

---

## 4. Phase 2: QLoRA Fine-Tuning Pipeline

### Prerequisites
Install training dependencies:
```bash
pip install -r training/requirements.txt
```

### Step 1: Run Supervised Fine-Tuning (SFT)
Fine-tune an open-weights model using 4-bit QLoRA and Hugging Face TRL:
```bash
python training/train_lora.py \
    --base_model "Qwen/Qwen2.5-7B-Instruct" \
    --train_data "training/data/redline_sft_train.jsonl" \
    --val_data "training/data/redline_sft_val.jsonl" \
    --output_dir "models/redline-llm-lora" \
    --epochs 3 \
    --batch_size 2 \
    --grad_accum 4 \
    --lr 2e-4
```

### Step 2: Run Direct Preference Optimization (DPO)
Align the fine-tuned adapter with the 4-Pillar Scoring Engine:
```bash
python training/train_dpo.py \
    --base_model "Qwen/Qwen2.5-7B-Instruct" \
    --adapter_path "models/redline-llm-lora" \
    --dpo_data "training/data/redline_dpo_train.jsonl" \
    --output_dir "models/redline-llm-dpo" \
    --epochs 2
```

### Step 3: Merge and Export Standalone Weights
Merge LoRA adapter weights into standalone SafeTensors and generate Ollama Modelfile:
```bash
python training/export_model.py \
    --base_model "Qwen/Qwen2.5-7B-Instruct" \
    --adapter_path "models/redline-llm-dpo" \
    --output_dir "models/redline-llm-final"
```

---

## 5. Google Colab / Remote GPU Runner

A ready-to-run Jupyter notebook is provided in [`training/Redline_LLM_FineTuning.ipynb`](file:///c:/Ashraf/Projects/RedlineProtocol/training/Redline_LLM_FineTuning.ipynb).
Alternatively, execute the full training script on any Linux/Colab GPU instance:
```bash
bash training/train_colab.sh
```

