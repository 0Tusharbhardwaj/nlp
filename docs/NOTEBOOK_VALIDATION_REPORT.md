# SecureCode AI — Notebook Cell-by-Cell Validation Report

**Date:** 2026-10-28  
**Audit Scope:** Exhaustive cell-by-cell inspection of all three Google Colab experiment notebooks.  
**Auditor:** Antigravity AI (Independent Research Auditor)

---

## 1. Executive Summary

This report documents the rigorous cell-by-cell audit of the three Google Colab notebooks generated for Phase 2:
1. `notebooks/02_full_scale_baselines.ipynb` (Classical Baselines: TF-IDF LR & Linear SVM)
2. `notebooks/03_codebert_full_scale_training.ipynb` (125M CodeBERT Fine-Tuning)
3. `notebooks/04_cross_dataset_evaluation.ipynb` (Cross-Dataset Evaluation Matrix E1–E4)

All 55 individual cells across the three notebooks were inspected for scientific validity, data leakage, mathematical correctness of metrics, checkpoint resilience, and local machine independence.

---

## 2. Notebook 1: `02_full_scale_baselines.ipynb` (17 Cells)

### Cell-by-Cell Audit Matrix

| Cell Index | Cell Type | Primary Function | Scientific & Engineering Audit | Finding Classification |
| :--- | :--- | :--- | :--- | :--- |
| **0** | Markdown | Title, Badges & Research Objectives | Details the Devign baseline formulation (21,854 train, 2,732 val, 2,732 test). Clean badges linking to Colab and GitHub. | Informational |
| **1** | Markdown | Step 1 Header | Describes Google Drive setup. | Informational |
| **2** | Code | Google Drive Mount & Path Resolution | Resolves `/content/drive/MyDrive/SecureCode-AI/baselines` or falls back to local `results/baselines`. Verified syntax. | Informational |
| **3** | Markdown | Step 2 Header | Dependencies and repo cloning. | Informational |
| **4** | Code | Git Clone & Dependency Installation | Clones `https://github.com/0Tusharbhardwaj/nlp.git` if missing; installs `scikit-learn`, `pandas`, `joblib`, `pyarrow`. Independent of local Windows paths. | Informational |
| **5** | Markdown | Step 3 Header | Dataset ingestion. | Informational |
| **6** | Code | Data Loading & Audit | Ingests `train.parquet` (21,854), `validation.parquet` (2,732), `test.parquet` (2,732). Verifies sample counts and class balance. | Informational |
| **7** | Markdown | Step 4 Header | Feature extraction. | Informational |
| **8** | Code | TF-IDF Vectorization | `TfidfVectorizer` fit strictly on `X_train` (`ngram_range=(1, 2)`, 50,000 features, sublinear TF). Transforms `X_val` and `X_test` without re-fitting. Zero data leakage. | Informational |
| **9** | Markdown | Step 5 Header | Logistic Regression training. | Informational |
| **10** | Code | LR Training & Validation Tuning | Evaluates $C \in [0.1, 0.5, 1.0, 2.0, 5.0]$ on the validation split using Macro F1. Test split remains untouched. | Informational |
| **11** | Markdown | Step 6 Header | Linear SVM training. | Informational |
| **12** | Code | Calibrated Linear SVM Training | Trains `LinearSVC(class_weight='balanced')` with `CalibratedClassifierCV(cv=3)` for valid probability output. | Informational |
| **13** | Markdown | Step 7 Header | Final test evaluation. | Informational |
| **14** | Code | Test Evaluation Function | Computes Accuracy, Precision, Recall, Macro F1, Binary F1, FNR, ROC-AUC on untouched test set. Formula for FNR: `fn / (fn + tp)`. Consistent confusion matrix orientation. | Informational |
| **15** | Markdown | Step 8 Header | Artifact export. | Informational |
| **16** | Code | Model, Metrics & Figure Export | Exports `.joblib` models, `baselines_devign_test_cm.png`, and `full_scale_baselines_metrics.json` to Drive. | Informational |

---

## 3. Notebook 2: `03_codebert_full_scale_training.ipynb` (21 Cells)

### Cell-by-Cell Audit Matrix

| Cell Index | Cell Type | Primary Function | Scientific & Engineering Audit | Finding Classification |
| :--- | :--- | :--- | :--- | :--- |
| **0** | Markdown | Title, Badges & Research Objectives | Details 125M CodeBERT fine-tuning protocol, hyperparameter specifications ($lr=2\times 10^{-5}$, AdamW, batch size 32, max len 512). | Informational |
| **1** | Markdown | Step 1 Header | Hardware acceleration. | Informational |
| **2** | Code | GPU Verification (`nvidia-smi`) | Checks CUDA availability, GPU device name, VRAM, and FP16 support. Warns user if running on CPU. | Informational |
| **3** | Markdown | Step 2 Header | Google Drive checkpointing. | Informational |
| **4** | Code | Directory Structure Mapping | Maps persistent checkpoint directory `/content/drive/MyDrive/SecureCode-AI/checkpoints/codebert_devign`. | Informational |
| **5** | Markdown | Step 3 Header | Dependencies & Git pull. | Informational |
| **6** | Code | Repository & Package Installation | Installs `transformers`, `datasets`, `accelerate`, `evaluate`, `scikit-learn`. | Informational |
| **7** | Markdown | Step 4 Header | Dataset loading. | Informational |
| **8** | Code | Partition Ingestion & Assertions | Strictly asserts sample counts: 21,854 train, 2,732 val, 2,732 test. Fails loudly if corrupted. Converts to Hugging Face `Dataset`. | Informational |
| **9** | Markdown | Step 5 Header | Tokenization. | Informational |
| **10** | Code | CodeBERT Tokenization | Maps `microsoft/codebert-base` tokenizer with `max_length=512, truncation=True, padding='max_length'`. | Informational |
| **11** | Markdown | Step 6 Header | Model initialization. | Informational |
| **12** | Code | Model & Metrics Definition | Initializes `AutoModelForSequenceClassification`. Custom `compute_metrics` implements Accuracy, Precision, Recall, Macro F1, Binary F1, FNR. Added single-class safety guard for ROC-AUC. | **Important (Fixed)** |
| **13** | Markdown | Step 7 Header | TrainingArguments configuration. | Informational |
| **14** | Code | Checkpoint Resumption & Trainer Setup | Checks `checkpoint_dir.glob('checkpoint-*')` and automatically resumes via `resume_from_checkpoint`. Uses `load_best_model_at_end=True, metric_for_best_model='macro_f1'`. | Informational |
| **15** | Markdown | Step 8 Header | Training execution. | Informational |
| **16** | Code | Execute Training (`trainer.train`) | Tracks elapsed wall-clock time and logs epoch-level evaluation loss. | Informational |
| **17** | Markdown | Step 9 Header | Final test split evaluation. | Informational |
| **18** | Code | Untouched Test Set Evaluation | Runs `trainer.evaluate(eval_dataset=tokenized_test)` strictly on the best checkpoint. | Informational |
| **19** | Markdown | Step 10 Header | Export artifacts. | Informational |
| **20** | Code | Model, Tokenizer, Metrics Export | Exports model weights, tokenizer, confusion matrix figure, and complete metrics JSON to Drive. | Informational |

---

## 4. Notebook 3: `04_cross_dataset_evaluation.ipynb` (17 Cells)

### Cell-by-Cell Audit Matrix

| Cell Index | Cell Type | Primary Function | Scientific & Engineering Audit | Finding Classification |
| :--- | :--- | :--- | :--- | :--- |
| **0** | Markdown | Title, Badges & Research Objectives | Documents research evaluation matrix: E1 (Devign in-distribution), E2 (LLMVul zero-shot), E3 (Mixed-train $\rightarrow$ LLMVul holdout), E4 (AI in-domain $\rightarrow$ LLMVul holdout), SeCodePLT transfer. | **Important (Corrected)** |
| **1** | Markdown | Step 1 Header | Drive mounting. | Informational |
| **2** | Code | Google Drive Mount & Path Resolution | Maps `/content/drive/MyDrive/SecureCode-AI/models`. | Informational |
| **3** | Markdown | Step 2 Header | Dependencies. | Informational |
| **4** | Code | Repo Setup & Package Install | Verifies environment packages. | Informational |
| **5** | Markdown | Step 3 Header | Dataset Ingestion. | Informational |
| **6** | Code | Cohort Loading & Verification | Ingests E1 (Devign test 2,732), E2 (LLMVul holdout 4,120), Gold (100 samples), SeCodePLT (2,480 samples). Verified zero repo overlap between training and holdout. | Informational |
| **7** | Markdown | Step 4 Header | Model Ingestion. | Informational |
| **8** | Code | Multi-Model Loader | Loads Devign-trained model, checks for presence of E3 (Mixed) and E4 (LLMVul-specific) fine-tuned weights in Drive. | **Important (Enhanced)** |
| **9** | Markdown | Step 5 Header | Inference Harness. | Informational |
| **10** | Code | Batched Inference Engine | Implements batch inference (`batch_size=32`), softmax probability generation, confusion matrix calculation, and single-class safe ROC-AUC computation. | Informational |
| **11** | Markdown | Step 6 Header | Execution of E1–E4. | Informational |
| **12** | Code | Run Evaluation Matrix | Runs inference on E1, E2, Gold, SeCodePLT, and conditionally evaluates E3 and E4 if model checkpoints exist. | Informational |
| **13** | Markdown | Step 7 Header | Domain Drop Analysis. | Informational |
| **14** | Code | Comparative Benchmark Table | Constructs side-by-side performance table. Computes $\Delta \text{Macro F1} = \text{F1}_{E2} - \text{F1}_{E1}$ and $\Delta \text{FNR}$. | Informational |
| **15** | Markdown | Step 8 Header | Figures and JSON Export. | Informational |
| **16** | Code | Export Figures & Results JSON | Plots dual confusion matrices and exports `cross_dataset_full_scale_results.json` to Google Drive. | Informational |

---

## 5. Summary of Deficiencies Identified & Remediation Status

| Issue ID | Affected Notebook | Audit Finding | Severity | Remediation Applied |
| :--- | :--- | :--- | :--- | :--- |
| **AUD-NB-01** | `03_codebert_full_scale_training.ipynb` | `compute_metrics` called `roc_auc_score(labels, probs)` without checking if `labels` contained both classes. | Important | Added `if len(set(labels)) > 1 else 0.5` guard. |
| **AUD-NB-02** | `04_cross_dataset_evaluation.ipynb` | Markdown table inverted E3 and E4 definitions relative to research audit standards. | Important | Re-aligned: E3 = Mixed Training $\rightarrow$ LLMVul Holdout; E4 = AI-Only Training $\rightarrow$ LLMVul Holdout. |
| **AUD-NB-03** | `04_cross_dataset_evaluation.ipynb` | Step 4 and Step 6 only loaded and evaluated the Devign-trained model, omitting dynamic loading for E3/E4 models. | Important | Added multi-model loader to evaluate E3 (`codebert_mixed_full`) and E4 (`codebert_llmvul_full`) models when available. |
| **AUD-NB-04** | All Notebooks | Verified independence from local Windows paths. | Informational | All notebooks clone repository and auto-download datasets from Hugging Face / GitHub if missing. |

---

## 6. Verification Status

All notebooks were regenerated via [`scripts/generate_colab_notebooks.py`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/scripts/generate_colab_notebooks.py) and validated as syntactically correct Jupyter Notebooks (v4.2 JSON format).
