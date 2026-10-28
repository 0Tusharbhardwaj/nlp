# SecureCode AI — Full-Scale Dataset Inventory

**Generated:** 2026-10-28 12:48:57 UTC  
**Scope:** Complete full-scale benchmark datasets for empirical vulnerability detection in human-authored and LLM-generated code.

---

## 1. Executive Summary

| Dataset ID | Full Benchmark Name | Source / Release | Format | Total Records | File Size | Task Formulation | Primary Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dataset A** | **CodeXGLUE / Devign** | Microsoft Research / Hugging Face | Parquet / JSONL | **27,318** | 22.3 MB | Binary Function Classification | Primary Human Training & Benchmark (E1) |
| **Dataset B** | **LLMVul** | Farhad & Dass (2024) / Wahed08 GitHub | CSV / JSONL | **21,430** | 46.2 MB | Multi-tool Consensus Classification | LLM Generalization & Cross-Domain (E2, E3, E4) |
| **Dataset C** | **SeCodePLT** | UCSB-SURFI (NeurIPS 2024) / Hugging Face | Parquet / JSONL | **1,240 tasks (2,480 pairs)** | 4.8 MB | Paired CVE Vulnerability Detection | Supplementary Zero-Shot Evaluation Cohort |

---

## 2. Partition & File Manifest

### Dataset A: CodeXGLUE / Devign
- **Train Split:** 21,854 samples | `datasets/raw/full/devign/train.parquet` (SHA256: `e319c83e2e816a10aeeebe78668aa95b757b04e555700bf5f826766b0e80bb06`)
- **Validation Split:** 2,732 samples | `datasets/raw/full/devign/validation.parquet` (SHA256: `a17a76ed040d7f8657d1ff741f967b44704c008101ac958e2990ad468203cfa4`)
- **Test Split:** 2,732 samples | `datasets/raw/full/devign/test.parquet` (SHA256: `259c944eb4f8689e83895de476a00fe4cadf4839636769e725d3744fc36cfcd5`)
- **Official Integrity:** Exact preserved splits as defined in Microsoft CodeXGLUE defect detection benchmark.

### Dataset B: LLMVul (Production LLM Benchmark)
- **Raw Release:** 21,430 functions across 226 production GitHub repositories | `datasets/raw/full/llmvul/LLMVul_v3-Updated.csv` (SHA256: `eb0efbf912fb22d51cddd33ffa11e6f3e4add56b52cc9e78dae96621c819c293`)
- **Clean Training Partition:** 14,631 functions (216 disjoint repositories) | `datasets/processed/llmvul_train_clean.jsonl`
- **Clean Holdout Partition:** 4,120 functions (8 disjoint repositories) | `datasets/processed/llmvul_test_clean.jsonl`
- **Quarantined Uncertain Partition:** 2,679 functions (tool disagreement / null label) | `datasets/processed/llmvul_uncertain.jsonl`
- **Expert Manual Review Gold Standard:** 100 functions (2 independent raters) | `datasets/processed/llmvul_manual_gold.jsonl`

### Dataset C: SeCodePLT (Supplementary C Benchmark)
- **Raw Release:** 1,240 paired C vulnerability tasks | `datasets/raw/full/secodeplt/c_vulnerability_detection.parquet` (SHA256: `835d78e675cc7302bdb955888405b756534ef4e11bd37304c6912e00946fbdee`)
- **Standardized Evaluation Cohort:** 2,480 evaluation samples (1,240 vulnerable + 1,240 safe) | `datasets/processed/secodeplt_eval.jsonl`
- **Adapter Class:** `src.data.secodeplt_adapter.SeCodePLTAdapter`
