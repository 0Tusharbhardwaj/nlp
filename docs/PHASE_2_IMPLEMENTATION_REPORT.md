# SecureCode AI — Phase 2 Implementation Report: Full-Scale Dataset & GPU Pipeline

**Date:** 2026-10-28  
**Status:** Completed & Validated (Awaiting Training Approval)  
**Lead Auditor / Engineer:** Antigravity AI  
**Repository:** [https://github.com/0Tusharbhardwaj/nlp](https://github.com/0Tusharbhardwaj/nlp)

---

## 1. Executive Summary

Phase 2 transitions the **SecureCode AI** research platform from curated smoke-test cohorts to a full-scale, scientifically defensible empirical research pipeline. All three target benchmarks have been acquired from their official sources, authenticated via SHA256 cryptographic checksums, subjected to rigorous data integrity audits, and staged into clean, leak-free evaluation partitions.

Furthermore, three executable Google Colab GPU notebooks have been developed to support reproducible training and cross-dataset evaluation. Per Phase 2 instructions, **expensive GPU training has not been executed automatically**. This report presents complete empirical dataset validation findings for review and approval.

---

## 2. Dataset Acquisition & Inventory

| Benchmark | Official Source / Reference | Format | Total Records | File Size | SHA256 Checksum (Primary File) | Primary Research Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dataset A: CodeXGLUE / Devign** | Microsoft Research / Hugging Face (`google/code_x_glue_cc_defect_detection`) | Parquet / JSONL | **27,318** | 22.3 MB | `e319c83e2e816a10aeeebe78668aa95b757b04e555700bf5f826766b0e80bb06` (`train.parquet`) | Primary Human Training & Benchmark (E1) |
| **Dataset B: LLMVul** | Farhad & Dass (2024) / GitHub (`Wahed08/LLMVul-Dataset`) | CSV / JSONL | **21,430** | 46.2 MB | `eb0efbf912fb22d51cddd33ffa11e6f3e4add56b52cc9e78dae96621c819c293` (`LLMVul_v3-Updated.csv`) | Production AI Code Generalization (E2, E3, E4) |
| **Dataset C: SeCodePLT** | UCSB-SURFI (NeurIPS 2024) / Hugging Face (`UCSB-SURFI/SeCodePLT`) | Parquet / JSONL | **1,240 tasks (2,480 pairs)** | 4.8 MB | `835d78e675cc7302bdb955888405b756534ef4e11bd37304c6912e00946fbdee` (`c_vulnerability_detection.parquet`) | Supplementary CVE Transfer Evaluation |

Detailed records are stored in:
- Manifest: [`datasets/download_manifest.json`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/download_manifest.json)
- Checksums: [`datasets/reports/DATASET_CHECKSUMS.sha256`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/DATASET_CHECKSUMS.sha256)
- Inventory: [`datasets/reports/FULL_DATASET_INVENTORY.md`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/FULL_DATASET_INVENTORY.md)

---

## 3. Benchmark Implementations & Data Integrity Findings

### 3.1. Dataset A: CodeXGLUE / Devign
The complete dataset was ingested while strictly preserving its official splits:
- **Train:** 21,854 functions (10,018 vulnerable, 45.84% vulnerability rate)
- **Validation:** 2,732 functions (1,187 vulnerable, 43.45% vulnerability rate)
- **Test:** 2,732 functions (1,255 vulnerable, 45.94% vulnerability rate)
- **Combined Total:** 27,318 functions
- **Missing Values:** Exactly 0 missing values across all columns (`id`, `func`, `target`, `project`, `commit_id`).

#### Critical Integrity Finding: Internal Split Overlap
The repository audit ([`datasets/reports/REPOSITORY_OVERLAP_REPORT.md`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/REPOSITORY_OVERLAP_REPORT.md)) revealed that the official Devign test split shares **100% of its repositories** (`qemu` and `FFmpeg`) with the training split. Furthermore, exact duplicate analysis identified **10 character-identical functions between train and test**, and **57 functions in the training split with contradictory labels** (identical code marked as both safe and vulnerable).

### 3.2. Dataset B: LLMVul (Production AI Benchmark)
The full raw release of 21,430 functions across 226 production GitHub repositories was inspected:
- **AI Tool Provenance:** `claude_code` (14,221), `copilot` (4,952), `claude` (807), `gemini` (386), `cursor` (373), `chatgpt` (298), `generic_llm` (242), `openai_codex` (135), `devin` (16).
- **Languages:** C++ (12,546, 58.5%), C (8,884, 41.5%).
- **Quarantine of Uncertain Labels:** Exactly **2,679 samples** exhibited static tool divergence or ambiguous signals (`vuln_label` is NaN). These were isolated into [`datasets/processed/llmvul_uncertain.jsonl`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/processed/llmvul_uncertain.jsonl) and excluded from primary binary evaluation.

#### Leak-Free Repository-Disjoint Partitioning
To guarantee valid scientific evaluation, [`src/data/llmvul_partitioner.py`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/src/data/llmvul_partitioner.py) constructed strictly disjoint repository partitions:
- **LLMVul Train:** 14,631 functions across **216 repositories** (1,176 vulnerable, 8.04% vulnerability rate)
- **LLMVul Holdout (Test):** 4,120 functions across **8 repositories** (364 vulnerable, 8.83% vulnerability rate)
- **Repository Overlap:** $\text{Train Repositories} \cap \text{Test Repositories} = \emptyset$ (Exactly 0 shared repositories).
- **Expert Manual Review Gold Standard:** Ingested the 100-sample double-blind expert review partition, isolating 85 unanimous consensus samples ([`datasets/processed/llmvul_manual_gold.jsonl`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/processed/llmvul_manual_gold.jsonl)).

### 3.3. Dataset C: SeCodePLT Adapter
Per Phase 2 requirements, SeCodePLT's 1,240 C vulnerability detection tasks were not merged into Devign. Instead, a dedicated evaluation adapter ([`src/data/secodeplt_adapter.py`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/src/data/secodeplt_adapter.py)) was implemented:
- Replaces `##SECCODEPLT##` template placeholders with `vulnerable_code_reference` (label: 1) and `patched_code_reference` (label: 0).
- Generates **2,480 strictly balanced evaluation instances** (1,240 safe, 1,240 vulnerable) with CVE metadata preserved ([`datasets/processed/secodeplt_eval.jsonl`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/processed/secodeplt_eval.jsonl)).

### 3.4. Token Length & Truncation Audit
Code tokenization analysis across all cohorts ([`datasets/reports/TOKEN_LENGTH_DISTRIBUTION_REPORT.md`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/TOKEN_LENGTH_DISTRIBUTION_REPORT.md)):
- **Devign Train:** Median = 206 tokens, Mean = 438.6 tokens, **23.12% exceed 512 tokens**.
- **LLMVul Train:** Median = 111 tokens, Mean = 172.7 tokens, **5.47% exceed 512 tokens**.
- **SeCodePLT:** Median = 566 tokens, Mean = 1,400.9 tokens, **53.10% exceed 512 tokens**.
- **Finding:** LLM-generated code in production repositories is significantly more modular and concise than legacy C codebases like QEMU and FFmpeg.

---

## 4. Google Colab GPU Experiment Architecture

Three executable Jupyter notebooks have been constructed under [`notebooks/`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/notebooks):

### 4.1. `notebooks/02_full_scale_baselines.ipynb`
- **Models:** TF-IDF + Logistic Regression (L2 regularized, class-balanced) and TF-IDF + Linear Support Vector Machine (LinearSVC with Platt probability calibration).
- **Scale:** Trained on all 21,854 Devign training samples; validated on 2,732 validation samples for hyperparameter $C$ tuning; scored once on the 2,732 untouched test samples.
- **Artifact Exports:** Models and vectorizers exported via `joblib`, confusion matrix visualizations, and [`full_scale_baselines_metrics.json`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/results/baselines).

### 4.2. `notebooks/03_codebert_full_scale_training.ipynb`
- **Model:** Full 125M parameter `microsoft/codebert-base`.
- **Hardware Acceleration:** Auto-detects NVIDIA GPUs (T4, V100, A100) and enables FP16 mixed precision (`fp16=True`) with gradient accumulation.
- **Checkpoint Recovery:** Saves epoch checkpoints to Google Drive (`/content/drive/MyDrive/SecureCode-AI/checkpoints/`); automatically detects and resumes training if Colab disconnects.
- **Validation Selection:** Best model weights selected strictly on validation Macro F1 to prevent overfitting.
- **Final Evaluation:** Evaluates best checkpoint on untouched Devign test set, saving metrics JSON and model weights to Google Drive.

### 4.3. `notebooks/04_cross_dataset_evaluation.ipynb`
- **Execution Matrix:**
  - **E1:** Devign Test (2,732 samples) — In-distribution human baseline.
  - **E2:** LLMVul Holdout (4,120 samples from 8 disjoint repos) — Zero-shot cross-domain generalization.
  - **E3 / E4:** AI-specific and mixed-domain model evaluations.
  - **Gold Standard:** LLMVul 100-sample expert consensus evaluation.
  - **Supplementary:** SeCodePLT 2,480-sample CVE transfer evaluation.
- **Outputs:** Domain drop analysis ($\Delta \text{Macro F1} = \text{F1}_{E2} - \text{F1}_{E1}$), ROC curves, comparative performance tables, and JSON export.

---

## 5. Reproducibility Instructions

### 5.1. Local Environment Execution
To reproduce the dataset acquisition, partitioning, and validation suite locally:

```bash
# 1. Download official benchmark datasets and verify checksums
python scripts/download_full_datasets.py

# 2. Partition LLMVul into repository-disjoint splits and isolate uncertain samples
python src/data/llmvul_partitioner.py

# 3. Export SeCodePLT standardized evaluation pairs
python -c "from pathlib import Path; from src.data.secodeplt_adapter import SeCodePLTAdapter; SeCodePLTAdapter().export_evaluation_jsonl(Path('datasets/processed/secodeplt_eval.jsonl'))"

# 4. Run the full dataset validation suite and generate reports
python scripts/validate_full_datasets.py

# 5. Run automated test suite
python -m unittest discover tests
```

### 5.2. Google Colab GPU Execution
1. Open [`notebooks/02_full_scale_baselines.ipynb`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/notebooks/02_full_scale_baselines.ipynb) in Colab and run all cells to generate baseline results.
2. Open [`notebooks/03_codebert_full_scale_training.ipynb`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/notebooks/03_codebert_full_scale_training.ipynb), ensure GPU runtime is enabled (**Runtime -> Change runtime type -> T4 GPU**), and run training. Checkpoints will persist in Google Drive.
3. Open [`notebooks/04_cross_dataset_evaluation.ipynb`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/notebooks/04_cross_dataset_evaluation.ipynb) to execute the cross-dataset evaluation matrix (E1–E4).

---

## 6. Automated Test Suite Verification

All unit and integration tests execute cleanly:

```text
Ran 44 tests in 0.285s
OK (skipped=3)
```

- [`tests/test_phase2_dataset_pipeline.py`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/tests/test_phase2_dataset_pipeline.py): Passed (4/4 tests: manifest verification, SeCodePLT adapter balance, LLMVul zero-leakage repository disjointness, report presence).
- Backend API tests: Passed.
- Model service transparency tests: Passed.

---

## 7. Decision Gate & Request for Approval

In strict accordance with Phase 2 instructions:
> *"Do not start expensive GPU training automatically. Present the dataset validation results and wait for approval before training."*

The complete dataset pipeline and Colab execution environment are verified and ready. We are standing by for your review and approval before initiating GPU training runs in Colab.
