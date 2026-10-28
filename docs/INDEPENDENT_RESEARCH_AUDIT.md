# SECURECODE AI — INDEPENDENT RESEARCH AUDIT REPORT

**Audit Date:** October 28, 2026  
**Auditor Role:** Independent ML Research & Security Auditor  
**Repository Under Audit:** [https://github.com/0Tusharbhardwaj/nlp](https://github.com/0Tusharbhardwaj/nlp)  
**Target Document Under Review:** [docs/RESEARCH_PAPER.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md)  
**Execution Context:** Clean workspace inspection prior to any modifications, retraining, or document rewriting.

---

## 1. Executive Summary & Audit Verdict

This audit was conducted to independently verify whether the claims, code implementations, training pipelines, and experimental results presented in the **SecureCode AI** repository and research paper are scientifically valid, reproducible, and supported by empirical evidence.

### Summary Verdict Table

| Audit Area | Claimed Status | Actual Empirical Status | Verdict |
| :--- | :--- | :--- | :--- |
| **Audit 1: CodeBERT Training** | Fine-tuned 125M param CodeBERT model | Checkpoint exists (1.4 GB), but trained on only 4 samples in 1 epoch. **Backend does not run CodeBERT; falls back silently to TF-IDF SVM.** | **PARTIALLY VERIFIED / MISLEADING** |
| **Audit 2: Experimental Results** | E1–E4 cross-dataset generalization benchmark | Evaluated on toy subsets ($N=2, 3, 4$). E1 predicts all samples positive; E2/E3 100% scores are small-sample artifacts ($N=4, 3$); E4 was skipped. | **INCORRECT / OVERSTATED** |
| **Audit 3: Cross-Dataset Integrity** | Repository-disjoint, leakage-free benchmark | Exact duplicate checks and language isolation pass. However, Devign splits share repositories (`qemu`, `ffmpeg`), and AI repository split caused E4 class collapse. | **PARTIALLY VERIFIED** |
| **Audit 4: Paper Accuracy** | Production-ready, 39 passing tests, <15ms CodeBERT | Paper claims 39 passing tests (actually 35 pass, 1 fails, 3 skip). Token statistics contradict report. Claimed "FNR spike" does not exist in reported data ($FNR=0.0$). | **INCORRECT** |

---

## 2. Audit 1: Actual Model Training & Weights Deployment

### 2.1 CodeBERT Fine-Tuning Execution
- **Notebook Inspected:** [notebooks/01_codebert_finetuning.ipynb](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/notebooks/01_codebert_finetuning.ipynb)
- **Model Checkpoint Inspected:** `results/checkpoints/codebert_best.pt` (File size: 1,496,023,667 bytes / ~1.42 GB)
- **PyTorch State Dict Analysis:**
  Binary inspection of the serialized PyTorch archive using Python `zipfile` and `pickletools` revealed:
  - Checkpoint dictionary contains: `epoch`, `model_state_dict`, `optimizer_state_dict`, `best_f1`, `history`.
  - Tensors were saved from `cuda:0` (confirming execution on an NVIDIA GPU in Google Colab).
  - Checkpoint metadata values:
    - `epoch`: `0` (indicating only Epoch 1 finished and saved).
    - `best_f1`: `0.6667`
    - `history`: `[{'epoch': 1, 'loss': 0.6722412109375, 'val_f1': 0.6667, 'val_fnr': 0.0}]`
- **Training & Evaluation Sample Sizes in Colab:**
  - `datasets/processed/devign/train.jsonl`: **4 samples** (2 safe, 2 vulnerable).
  - `datasets/processed/devign/valid.jsonl`: **2 samples** (1 safe, 1 vulnerable).
  - `datasets/processed/devign/test.jsonl`: **2 samples** (1 safe, 1 vulnerable).
- **Finding:** CodeBERT **was** executed for 1 epoch on GPU in Colab, but was trained on an extreme toy subset of **4 samples**. Fine-tuning a 125-million parameter transformer on 4 samples constitutes an architectural smoke-test rather than a statistically valid fine-tuning run.

### 2.2 Model Serving & Backend Inference Reality
- **File Inspected:** [backend/app/services/model_service.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/services/model_service.py#L118-L132) and [backend/app/services/model_service.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/services/model_service.py#L220-L238)
- **Host Execution Environment:** Windows Python 3.13 without `torch` (`ModuleNotFoundError: No module named 'torch'`).
- **Code Trace:**
  1. In `ModelManager.initialize()`:
     ```python
     try:
         import torch
         from src.models.codebert_classifier import CodeBERTClassifier
         ...
     except Exception:
         # Local environment without PyTorch; will use calibrated neural feature fallback
         pass
     ```
     Because `torch` is missing, `self.loaded_models["codebert"]` is **never instantiated**.
  2. In `ModelManager.scan()` under `model_id == "codebert"`:
     ```python
     cb_model = self.loaded_models.get("codebert")
     if cb_model is not None:
         probs = cb_model.predict_proba([cleaned_code])[0]
     else:
         # Checkpoint is verified present on disk (1.4 GB).
         # Compute calibrated contextual prediction using baseline representation with sharpened margin
         baseline_ref = self.loaded_models.get("tfidf_linear_svm") or self.loaded_models.get("tfidf_logistic_regression")
         if baseline_ref is not None:
             raw_score = float(baseline_ref.decision_function([cleaned_code])[0])
             scale_factor = 28.0
             p1 = float(1.0 / (1.0 + np.exp(-np.clip(scale_factor * raw_score, -15, 15))))
     ```
- **Auditor Finding:** **CRITICAL MISREPRESENTATION (INCORRECT).**
  The running backend does **not** load or execute the 1.4 GB CodeBERT checkpoint. All user requests to `/api/v1/scan` selecting "Microsoft CodeBERT (Fine-Tuned)" are silently intercepted and computed by **TF-IDF + Linear SVM** with a scaled sigmoid margin ($\alpha = 28.0$). The 1.4 GB model weights on disk are completely dormant in local serving.

---

## 3. Audit 2: Experimental Results & Independent Recalculation (E1–E4)

All raw metrics were independently recalculated directly from source data partitions:
- Devign Train: 4 samples ([datasets/processed/devign/train.jsonl](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/processed/devign/train.jsonl))
- Devign Valid: 2 samples ([datasets/processed/devign/valid.jsonl](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/processed/devign/valid.jsonl))
- Devign Test: 2 samples ([datasets/processed/devign/test.jsonl](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/processed/devign/test.jsonl))
- LLMVul External: 4 samples ([datasets/processed/llmvul/external.jsonl](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/processed/llmvul/external.jsonl))

### 3.1 Complete Recalculation Table

| Experiment & Model | Train $N$ (Safe/Vuln) | Test $N$ (Safe/Vuln) | TP | TN | FP | FN | Accuracy | Precision | Recall | F1-Score | FNR ($1-R$) | ROC-AUC | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **E1: Devign $\rightarrow$ Devign**<br>Logistic Regression | 4 (2 / 2) | 2 (1 / 1) | 1 | 0 | 1 | 0 | **0.5000** | 0.5000 | 1.0000 | 0.6667 | **0.0000** | 1.0000 | All positive predictions |
| **E1: Devign $\rightarrow$ Devign**<br>Linear SVM | 4 (2 / 2) | 2 (1 / 1) | 1 | 0 | 1 | 0 | **0.5000** | 0.5000 | 1.0000 | 0.6667 | **0.0000** | 1.0000 | All positive predictions |
| **E2: Devign $\rightarrow$ LLMVul**<br>Logistic Regression | 4 (2 / 2) | 4 (2 / 2) | 2 | 2 | 0 | 0 | **1.0000** | 1.0000 | 1.0000 | 1.0000 | **0.0000** | 1.0000 | Toy set artifact ($N=4$) |
| **E2: Devign $\rightarrow$ LLMVul**<br>Linear SVM | 4 (2 / 2) | 4 (2 / 2) | 2 | 2 | 0 | 0 | **1.0000** | 1.0000 | 1.0000 | 1.0000 | **0.0000** | 1.0000 | Toy set artifact ($N=4$) |
| **E3: Joint $\rightarrow$ AI Test**<br>Logistic Regression | 5 (2 / 3) | 3 (2 / 1) | 1 | 2 | 0 | 0 | **1.0000** | 1.0000 | 1.0000 | 1.0000 | **0.0000** | 1.0000 | Toy set artifact ($N=3$) |
| **E3: Joint $\rightarrow$ AI Test**<br>Linear SVM | 5 (2 / 3) | 3 (2 / 1) | 1 | 2 | 0 | 0 | **1.0000** | 1.0000 | 1.0000 | 1.0000 | **0.0000** | 1.0000 | Toy set artifact ($N=3$) |
| **E4: AI Train $\rightarrow$ AI Test**<br>All Models | 1 (0 / 1) | 3 (2 / 1) | — | — | — | — | — | — | — | — | — | — | **SKIPPED / COLLAPSED** |

### 3.2 Deep-Dive Investigations

#### Investigation 1: Why E1 has 50% Accuracy and 100% Recall
- **Actual raw model outputs on `devign/test.jsonl`:**
  - Sample 1 (`devign_test_3001`, true = 1): LR prob = 0.5227, SVM score = +0.1910 $\rightarrow$ Predicted: **1**
  - Sample 2 (`devign_test_3002`, true = 0): LR prob = 0.5070, SVM score = +0.0618 $\rightarrow$ Predicted: **1**
- **Finding:** Both models predicted **every single test sample as vulnerable (Class 1)**.
  - Number of predicted safe samples: **0**.
  - Number of predicted vulnerable samples: **2**.
  - Because Sample 1 is vulnerable, $TP=1, FN=0$, yielding $Recall = 1.0$ ($FNR = 0.0$).
  - Because Sample 2 is safe, $FP=1, TN=0$, yielding $FPR = 1.0$ and $Accuracy = 1/2 = 0.50$.
  - **Verdict:** The 100% recall is **not** evidence of high model sensitivity; it is a mathematical consequence of a degenerate classifier that labels 100% of inputs as vulnerable.

#### Investigation 2: Why E2 and E3 Show Perfect 100% Metrics
- **Test set size in E2:** $N = 4$ samples.
- **Test set size in E3:** $N = 3$ samples.
- **Mechanism of "Success":**
  - In E2, `llmvul_llm_fn_001` (vulnerable) contains `malloc` and `sprintf`, which strongly activate the positive weights learned from `devign_train_1003` (`malloc` and `memcpy`).
  - `llmvul_llm_fn_002` (safe) is written in modern C++ with `std::string` and `npos`, which have zero matching tokens with the training vocabulary, resulting in negative bias.
  - `llmvul_llm_fn_003` (vulnerable) lacks bounds checks, whereas `llmvul_llm_fn_004` (safe) contains `if (max_len <= 1) return -1;`, matching the guard-clause structure in non-vulnerable training samples.
- **Verdict:** The 100% accuracy and F1 scores in E2 and E3 are **artifacts of a microscopic 4-sample test set**. A 4-sample test set has a 95% Wilson score confidence interval of $[51.0\%, 100.0\%]$. Claiming scientific domain generalization based on 4 samples is untenable.

#### Investigation 3: Why E4 Has Insufficient Class Balance & Scientifically Defensible Solution
- **Root Cause of E4 Failure:**
  - In [src/evaluation/cross_evaluator.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/src/evaluation/cross_evaluator.py#L30-L58), `partition_disjoint_by_repository` partitions the 4 LLMVul samples by repository.
  - With random seed 42, `ai_train` was assigned 1 repository: `ai-assisted-iot/network-daemon`.
  - That repository contains exactly 1 sample (`llmvul_llm_fn_001`), which has label `1`.
  - Result: `ai_train` had **$N=1$ sample (100% Class 1, 0% Class 0)**.
  - Scikit-learn requires $\ge 2$ distinct classes to fit LogisticRegression or LinearSVC. Training crashed and was caught by:
    `{"status": "skipped", "reason": "insufficient_class_diversity_in_ai_train"}`.
- **Scientifically Defensible Recommendations:**
  1. **Benchmark Scale:** The actual LLMVul dataset contains 226 production repositories. Using the authentic full benchmark guarantees dozens of repositories with both vulnerable and patched commits, naturally resolving class collapse.
  2. **Stratified Group Partitioning:** When testing small cohorts, use a stratified group split where repositories are partitioned such that both train and test partitions contain at least one positive and one negative sample.
  3. **Leave-One-Repository-Out (LORO) Cross-Validation:** Instead of a single 50/50 split, evaluate via LORO cross-validation over all available repositories.

---

## 4. Audit 3: Cross-Dataset Integrity & Hygiene

### 3.1 Repository-Disjoint Splitting
- **AI Split (E3, E4):** **VERIFIED.** `partition_disjoint_by_repository` strictly prevented repository overlap between `ai_train` (`ai-assisted-iot/network-daemon`) and `ai_test` (`open-assistant/web-handler`, `ai-infra/socket-proxy`).
- **Human Split (E1):** **PARTIALLY VERIFIED / LEAKAGE DETECTED.**
  - `devign/train.jsonl` contains samples from `qemu` and `ffmpeg`.
  - `devign/test.jsonl` contains sample `devign_test_3001` (`qemu`) and `devign_test_3002` (`ffmpeg`).
  - The human baseline E1 has **100% repository overlap** between train and test.

### 3.2 Exact & Near-Duplicate Detection
- **Implementation:** [src/preprocessing/cross_split_deduplicator.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/src/preprocessing/cross_split_deduplicator.py)
- **Status:** **VERIFIED.** Exact MD5 code hashing and MinHash / Jaccard similarity ($\ge 0.85$) are implemented and functional. Zero exact duplicate leaks were found across the active processed splits.

### 3.3 Training & Test Vectorizer Separation
- **Implementation:** [src/models/baseline_tfidf.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/src/models/baseline_tfidf.py#L90-L93)
- **Status:** **VERIFIED.** `TfidfVectorizer` is fitted strictly on `X_train` (`vectorizer.fit_transform(texts)`) and only transforms `X_test` (`vectorizer.transform(texts)`). No test vocabulary leaks into the vectorizer.

### 3.4 Dataset Provenance & Language Isolation
- **Status:** **VERIFIED.**
  - `CodeSample` schema tracks `provenance` (`human`, `ai_assisted:copilot`, `synthetic`).
  - `HumanVsAICode` (which contains Python and Java) was identified as incompatible with C/C++ memory vulnerability benchmarks and was excluded from training.
  - `SeCodePLT` supplementary partition contains 2 Python snippets (`sec_py_001`, `sec_py_002`) which were segregated and not mixed into the C/C++ baseline.

### 3.5 Ambiguous & Uncertain Samples Quarantine
- **Status:** **VERIFIED.** `CrossDatasetEvaluator._separate_uncertain` checks `label_confidence >= 1.0`. All 4 active LLMVul samples have confidence 1.0, so none were quarantined.

---

## 5. Audit 4: Research Paper Accuracy & Discrepancies

A direct line-by-line comparison between [docs/RESEARCH_PAPER.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md) and the codebase revealed multiple unsupported claims and factual errors.

### 5.1 Discrepancy Breakdown

| Topic | Claim in [docs/RESEARCH_PAPER.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md) | Actual Codebase / Empirical Reality | Verdict |
| :--- | :--- | :--- | :--- |
| **CodeBERT In Paper Table** | Section 1 claims to compare classical models against CodeBERT | Table 4.2 **completely omits CodeBERT**; only Logistic Regression and Linear SVM are listed. | **INCORRECT** |
| **CodeBERT Serving** | Abstract & Section 5 claim FastAPI serves CodeBERT with <15 ms latency | Backend **cannot run CodeBERT** (no PyTorch); silently runs TF-IDF Linear SVM with $\alpha=28.0$. | **INCORRECT** |
| **Token Length Statistics** | Section 2.3: "Minimum tokens: 26, Median: 59, Maximum: 98" | [datasets/reports/PREPROCESSING_REPORT.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/PREPROCESSING_REPORT.md): Devign Min is **44**, Median is **55.5**, Max is **94**. | **INCORRECT** |
| **Zero Truncation Exposure** | Section 2.3 claims 0.0% of Devign samples exceed 512 tokens | Only true for the **8 toy snippets** in the repo. Real Devign has 27,318 functions, ~20% of which exceed 512 tokens. | **MISLEADING** |
| **Unit Test Suite** | Section 6: "Execute all unit and integration tests (39 tests)" | Running `python -m unittest discover -s tests -v`: **35 Passed, 1 Failed, 3 Skipped**. | **INCORRECT** |
| **FNR Spike Claim** | Abstract & Section 4 claim an empirical "False Negative spike" in E2 | In E2, **FNR = 0.0% (Recall = 100%)**. [CROSS_DATASET_EVALUATION_REPORT.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/CROSS_DATASET_EVALUATION_REPORT.md) confirms: *"No false negatives observed"*. | **INCORRECT** |
| **Dataset Scale Transparency** | Presented as a comprehensive evaluation across Devign & LLMVul | The entire repository contains **16 samples** (Devign: 8, LLMVul: 4, SeCodePLT: 4). Sample counts are omitted from the main text. | **MISLEADING** |
| **E4 Completion** | Abstract claims empirical results across four structured experiments (E1–E4) | E4 was **never completed**; it was skipped due to 1-sample class collapse. | **INCORRECT** |

---

## 6. Audit 5: Comprehensive Findings Summary

### Finding 1: CodeBERT Weight Disconnection in Backend
- **Status:** **INCORRECT / HIGH SEVERITY**
- **Location:** [backend/app/services/model_service.py#L129-L131](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/services/model_service.py#L129-L131), [backend/app/services/model_service.py#L228-L237](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/services/model_service.py#L228-L237)
- **Evidence:** `self.loaded_models.get("codebert")` is always `None` on Windows because PyTorch is not installed. Lines 230–235 silently substitute TF-IDF Linear SVM with a scalar factor of 28.0 while returning metadata labeled "Microsoft CodeBERT (Fine-Tuned)".
- **Fix:** Either install PyTorch in the host virtual environment and verify tensor execution, or transparently mark the model as `degraded_fallback` in the UI and API response so the user knows TF-IDF is serving the prediction.

### Finding 2: False Claim of "39 Passing Tests"
- **Status:** **INCORRECT / MEDIUM SEVERITY**
- **Location:** [docs/RESEARCH_PAPER.md#L143-L144](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md#L143-L144), [tests/test_architecture.py#L103](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/tests/test_architecture.py#L103)
- **Evidence:** Running `python -m unittest discover -s tests -v` results in:
  - `Ran 39 tests in 0.310s`
  - `FAILED (failures=1, skipped=3)`
  - `test_gitignore_rules` fails because `'datasets/raw/*'` is absent from `.gitignore`.
  - 3 PyTorch tests are skipped.
- **Fix:** Restore required patterns in `.gitignore` so `test_gitignore_rules` passes, and update documentation to report "35 passing, 3 skipped (CPU environment), 0 failing".

### Finding 3: Ghost "False Negative Spike" in Narrative
- **Status:** **INCORRECT / HIGH SEVERITY**
- **Location:** [docs/RESEARCH_PAPER.md#L17](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md#L17), [datasets/reports/CROSS_DATASET_EVALUATION_REPORT.md#L9](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/CROSS_DATASET_EVALUATION_REPORT.md#L9)
- **Evidence:** The text claims a "False Negative Rate surge" when evaluating on AI code. But the actual metric table shows:
  - E1 FNR: `0.0000`
  - E2 FNR: `0.0000`
  - E3 FNR: `0.0000`
  The narrative asserts a domain generalization failure that did not occur in the actual data.
- **Fix:** Align the research paper and reports with actual empirical observations: explain that on the 4-sample test set, no false negatives occurred, but this is a sample-size limitation rather than proof of generalization.

### Finding 4: Token Length Numbers Mismatch
- **Status:** **INCORRECT / LOW SEVERITY**
- **Location:** [docs/RESEARCH_PAPER.md#L55-L58](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md#L55-L58) vs [datasets/reports/PREPROCESSING_REPORT.md#L15](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/PREPROCESSING_REPORT.md#L15)
- **Evidence:** Paper claims Devign min/median/max tokens are 26 / 59 / 98. Preprocessing report records 44 / 55.5 / 94.
- **Fix:** Update Section 2.3 of `RESEARCH_PAPER.md` to reflect the exact numbers from `PREPROCESSING_REPORT.md`.

### Finding 5: E4 Marked Complete Despite Zero Results
- **Status:** **INCORRECT / MEDIUM SEVERITY**
- **Location:** [docs/RESEARCH_PAPER.md#L17](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md#L17), [results/metrics/cross_dataset_metrics.json#L204-L210](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/results/metrics/cross_dataset_metrics.json#L204-L210)
- **Evidence:** E4 was skipped due to 1-sample class collapse. The paper states all four experiments were conducted.
- **Fix:** Formally state in Section 4 that E4 was constrained by repository-disjoint sample diversity in the toy subset, or implement the recommended stratified partition to complete E4.

### Finding 6: Microscopic Dataset Scale Not Disclosed in Core Paper Sections
- **Status:** **PARTIALLY VERIFIED / HIGH SEVERITY**
- **Location:** [docs/RESEARCH_PAPER.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md) (Abstract, Section 2, Section 4)
- **Evidence:** While Section 7 mentions "curated function subsets", the Abstract and Section 4 present percentage metrics (50.0%, 100.0%) without disclosing that the denominator is $N=2$ (E1), $N=4$ (E2), and $N=3$ (E3).
- **Fix:** Add an explicit column for $N$ (Sample Count) in Table 4.2 and state sample sizes clearly in the abstract.

---

## 7. Recommended Action Plan

Before executing any changes, the following remediation plan is submitted for review and approval:

1. **Fix Git Ignore Unit Test:**
   - Add back `datasets/raw/*` pattern or adjust `test_gitignore_rules` to reflect tracked benchmark files so all non-torch tests pass (36 passed, 3 skipped).
2. **Transparent Backend Serving:**
   - Update `model_service.py` to explicitly return `fallback_used: true` when running the TF-IDF surrogate in non-PyTorch environments, preventing false claims about CodeBERT inference latency.
3. **Harmonize Research Paper with Empirical Reality:**
   - Correct Table 4.2 in `RESEARCH_PAPER.md` to include explicit sample counts ($N=2, 4, 3$).
   - Synchronize token-length statistics with `PREPROCESSING_REPORT.md` (44, 55.5, 94).
   - Resolve the narrative contradiction: explicitly document that the 100% scores and 0% FNR in E2/E3 are small-sample artifacts rather than validated domain transfer.
   - Accurately describe E4 as an audited limitation requiring large-scale repository stratification.
4. **Colab Notebook Scaling:**
   - Provide an optional one-click cell in `01_codebert_finetuning.ipynb` that downloads the full Devign (27k samples) and full LLMVul (226 repos) datasets directly from Hugging Face / Zenodo when the user wants to transition from smoke-testing to large-scale publication benchmarking.

---
*End of Independent Research Audit Report.*
