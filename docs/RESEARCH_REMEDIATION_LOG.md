# SECURECODE AI — RESEARCH REMEDIATION LOG (PHASE 1)

**Date:** October 28, 2026  
**Auditor / Remediation Engineer:** Antigravity AI  
**Scope:** Phase 1 Safe Engineering Corrections & Research Transparency Audit  
**Target Repository:** [https://github.com/0Tusharbhardwaj/nlp](https://github.com/0Tusharbhardwaj/nlp)  

---

## 1. Executive Summary of Phase 1 Remediation

Following the findings documented in [docs/INDEPENDENT_RESEARCH_AUDIT.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/INDEPENDENT_RESEARCH_AUDIT.md), Phase 1 was executed with strict adherence to scientific integrity constraints:
- **Zero fabrication of results.**
- **Zero silent modification of experimental metrics.**
- **Zero deletion of existing checkpoints, models, or datasets.**
- **Preservation of existing architecture and working components.**

All safe engineering corrections requested have been implemented, tested, and validated.

---

## 2. Engineering Corrections Implemented

### 2.1 Transparent Model Inference (No Masked Predictions)
* **Problem:** In [backend/app/services/model_service.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/services/model_service.py), when CodeBERT could not load due to the absence of `torch` in the local CPU environment, the backend silently used TF-IDF Linear SVM with an artificial multiplier ($\alpha = 28.0$) while labeling the response as "Microsoft CodeBERT".
* **Corrections Applied:**
  1. **Removed Artificial Simulation:** Completely deleted the surrogate prediction block in `model_service.py`.
  2. **Explicit Model Availability:** In `ModelManager.initialize()`, if the 1.4 GB checkpoint exists on disk but the PyTorch runtime is absent, the model status is explicitly set to:
     `runtime_unavailable (PyTorch runtime not loaded: ModuleNotFoundError)` instead of misleadingly claiming `"ready"`.
  3. **Strict Error Handling by Default:** If a client requests `model_id: "codebert"` without explicitly enabling fallback, the API returns an explicit **HTTP 503 Service Unavailable** with a descriptive message informing the caller that the PyTorch runtime is not installed.
  4. **Transparent Fallback Attribution:** Added `allow_fallback: bool = False` to `ScanRequest` and `BatchScanRequest`. If and only if the caller explicitly sets `allow_fallback: true`, the system executes an available classical baseline model, setting:
     - `requested_model: "codebert"`
     - `actual_model: "tfidf_linear_svm"`
     - `fallback_used: True`
     - `model_name: "TF-IDF + Linear SVM (Transparent Fallback for CodeBERT)"`
  5. **Schema Updates:** Added `requested_model`, `actual_model`, and `fallback_used` fields to [backend/app/schemas/scan.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/schemas/scan.py) and [frontend/src/types/api.ts](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/frontend/src/types/api.ts).
  6. **UI Transparency:** Updated [frontend/src/components/ScannerTab.tsx](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/frontend/src/components/ScannerTab.tsx) to display `(PyTorch Missing)` in the model dropdown when runtime is absent and render an alert banner when transparent fallback is invoked.

### 2.2 Fix Failing Architecture Test (`.gitignore`)
* **Problem:** `test_gitignore_rules` in [tests/test_architecture.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/tests/test_architecture.py) failed because `datasets/raw/*` and `datasets/processed/*` had been removed from `.gitignore` to allow tracking of sample files.
* **Corrections Applied:**
  Updated [.gitignore](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/.gitignore) to include:
  ```gitignore
  datasets/raw/*
  datasets/processed/*
  !datasets/raw/*/*.jsonl
  !datasets/processed/*/*.jsonl
  !datasets/processed/*/*.json
  !datasets/raw/**/.gitkeep
  !datasets/processed/**/.gitkeep
  ```
  This satisfies the test rule while preserving the committed JSONL benchmark samples.
* **Test Outcome:** `test_gitignore_rules` passes cleanly.

### 2.3 Experiment Integrity in Reports
* **Problem:** [datasets/reports/CROSS_DATASET_EVALUATION_REPORT.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/CROSS_DATASET_EVALUATION_REPORT.md) previously asserted an empirical "False Negative surge" while reporting $FNR = 0.0000$ and omitted sample counts ($N$).
* **Corrections Applied:**
  Updated [scripts/run_cross_evaluation.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/scripts/run_cross_evaluation.py) and regenerated the report to explicitly categorize:
  1. **Completed Full-Scale Experiments:** None (pending execution on full-scale dataset on GPU).
  2. **Smoke Tests (Pipeline Verification):** E1, E2, E3 (evaluated on local curated cohorts of $N=2..4$ to verify pipeline mechanics, comment stripping, and leakage-free vectorization).
  3. **Incomplete Experiments:** E4 (skipped due to 1-sample class collapse, $N_0=0$).
  4. **Awaiting Full Scale:** E1–E4 on complete CodeXGLUE (27k samples) and LLMVul (226 repos).
  5. **Sample Count Columns:** Explicitly added Train $N$ and Test $N$ columns to the summary table.

---

## 3. Review of `docs/RESEARCH_PAPER.md`: Unsupported Claims & Necessary Corrections

As directed, [docs/RESEARCH_PAPER.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md) was **not** rewritten in this phase. The following list identifies every unsupported claim and the exact modification required in Phase 2:

| Paper Section | Exact Text in Paper | Scientific Issue | Required Remediation in Paper |
| :--- | :--- | :--- | :--- |
| **Abstract (L16–L18)** | *"evaluate classical lexical models... against Microsoft CodeBERT fine-tuned with class-balanced cross-entropy loss."* | CodeBERT was fine-tuned on only 4 samples in Colab and is omitted from the results table. | Clarify that CodeBERT was validated via a proof-of-concept pipeline in Colab, while systematic local cross-dataset evaluation focused on classical baselines. |
| **Abstract (L17)** | *"the False Negative Rate (FNR = 1 - Recall) serves as the paramount safety metric."* Narrative implies an observed surge. | In actual E1–E3 experiments, $FNR = 0.0000$. There is no observed surge in the data. | State that while FNR is theoretically critical, the small-cohort evaluation yielded 0% FNR due to sample size constraints ($N=2..4$). |
| **Section 2.3 (L55–L58)** | *"Minimum tokens: 26, Median tokens: 59, Maximum tokens: 98"* | Contradicts [datasets/reports/PREPROCESSING_REPORT.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/PREPROCESSING_REPORT.md), which records Min: 44, Median: 55.5, Max: 94. | Synchronize statistics to match `PREPROCESSING_REPORT.md` exactly: Min: 44, Median: 55.5, Max: 94. |
| **Section 2.3 (L58)** | *"Percentage exceeding 512 tokens: 0.0%. This validates that truncation bias does not confound our contextual CodeBERT evaluations."* | 0.0% is true only for the 8 short toy functions in the repo. Real Devign has 27,318 functions, ~20% of which exceed 512 tokens. | Explicitly contextualize that zero truncation holds for the local evaluation subset, but full CodeXGLUE requires sequence truncation policies. |
| **Section 4.2 (Table 4.2)** | Reports Accuracy, Precision, Recall, F1, FNR without $N$ counts. | Omits sample sizes ($N=2, 4, 3$), making toy prototype results look like large-scale benchmark results. | Add columns for **Train $N$** and **Test $N$**, and label the evaluation cohort as a *Local Pipeline Smoke-Test Cohort*. |
| **Section 4.2 (Table 4.2)** | *"E4: AI-Native Holdout \| Audited Holdout \| — \| — \| —"* | E4 was skipped due to 1-sample class collapse, but the paper implies it was an evaluated setting. | Explicitly label E4 as *Incomplete / Awaiting Multi-Repository Benchmark*. |
| **Section 5 (L119)** | *"Sub-15 millisecond response latency for single and batch scan requests."* | Only true for TF-IDF. CodeBERT requires 150–500 ms on CPU. Prior backend faked CodeBERT latency using TF-IDF SVM. | Clarify that sub-15 ms latency applies to classical TF-IDF models; CodeBERT inference requires GPU acceleration for real-time serving. |
| **Section 6 (L143)** | *"Execute all unit and integration tests (39 tests)"* | Running the test suite currently executes 40 tests: 37 passed, 3 skipped (due to local CPU-only PyTorch guards). | Update text to: *"Execute test suite: 40 automated tests (37 passed, 3 skipped in CPU environments without PyTorch, 0 failing)"*. |

---

## 4. Test Suite Execution Results

Ran complete test suite after implementing all Phase 1 corrections:
```bash
python -m unittest discover -s tests -v
```

### Exact Output:
```text
test_batch_scan (test_api.TestAPIEndpoints.test_batch_scan) ... ok
test_codebert_unavailable_and_transparent_fallback (test_api.TestAPIEndpoints.test_codebert_unavailable_and_transparent_fallback) ... ok
test_datasets_endpoint (test_api.TestAPIEndpoints.test_datasets_endpoint) ... ok
test_experiments_endpoints (test_api.TestAPIEndpoints.test_experiments_endpoints) ... ok
test_health_endpoints (test_api.TestAPIEndpoints.test_health_endpoints) ... ok
test_list_and_get_models (test_api.TestAPIEndpoints.test_list_and_get_models) ... ok
test_root_endpoint (test_api.TestAPIEndpoints.test_root_endpoint) ... ok
test_scan_validation_errors (test_api.TestAPIEndpoints.test_scan_validation_errors) ... ok
test_single_scan_linear_svm (test_api.TestAPIEndpoints.test_single_scan_linear_svm) ... ok
test_single_scan_logistic_regression (test_api.TestAPIEndpoints.test_single_scan_logistic_regression) ... ok
test_config_loader_and_schema (test_architecture.TestProjectArchitecture.test_config_loader_and_schema) ... ok
test_core_files_exist (test_architecture.TestProjectArchitecture.test_core_files_exist) ... ok
test_directory_structure_exists (test_architecture.TestProjectArchitecture.test_directory_structure_exists) ... ok
test_gitignore_rules (test_architecture.TestProjectArchitecture.test_gitignore_rules) ... ok
test_compute_vulnerability_metrics (test_baselines.TestBaselines.test_compute_vulnerability_metrics) ... ok
test_model_save_and_load (test_baselines.TestBaselines.test_model_save_and_load) ... ok
test_no_test_leakage_in_vectorizer (test_baselines.TestBaselines.test_no_test_leakage_in_vectorizer) ... ok
test_tfidf_linear_svm (test_baselines.TestBaselines.test_tfidf_linear_svm) ... ok
test_tfidf_logistic_regression (test_baselines.TestBaselines.test_tfidf_logistic_regression) ... ok
test_checkpoint_save_and_structure (test_codebert_training.TestCodeBERTTraining.test_checkpoint_save_and_structure) ... skipped 'PyTorch not installed in local environment'
test_codebert_classifier_wrapper_fallback (test_codebert_training.TestCodeBERTTraining.test_codebert_classifier_wrapper_fallback) ... ok
test_compute_class_weights (test_codebert_training.TestCodeBERTTraining.test_compute_class_weights) ... skipped 'PyTorch not installed in local environment'
test_load_codebert_split_data (test_codebert_training.TestCodeBERTTraining.test_load_codebert_split_data) ... ok
test_vulnerability_dataset (test_codebert_training.TestCodeBERTTraining.test_vulnerability_dataset) ... skipped 'PyTorch not installed in local environment'
test_cross_dataset_evaluator_runs_e1_to_e4 (test_cross_evaluation.TestCrossDatasetEvaluation.test_cross_dataset_evaluator_runs_e1_to_e4) ... ok
test_partition_disjoint_by_repository (test_cross_evaluation.TestCrossDatasetEvaluation.test_partition_disjoint_by_repository) ... ok
test_analyzer_missing_values_and_labels (test_data_loaders.TestDataLoadersAndAnalysis.test_analyzer_missing_values_and_labels) ... ok
test_code_sample_validation (test_data_loaders.TestDataLoadersAndAnalysis.test_code_sample_validation) ... ok
test_cross_dataset_overlap (test_data_loaders.TestDataLoadersAndAnalysis.test_cross_dataset_overlap) ... ok
test_devign_loader (test_data_loaders.TestDataLoadersAndAnalysis.test_devign_loader) ... ok
test_exact_and_near_duplicates (test_data_loaders.TestDataLoadersAndAnalysis.test_exact_and_near_duplicates) ... ok
test_human_vs_ai_loader (test_data_loaders.TestDataLoadersAndAnalysis.test_human_vs_ai_loader) ... ok
test_llmvul_loader (test_data_loaders.TestDataLoadersAndAnalysis.test_llmvul_loader) ... ok
test_secodeplt_loader (test_data_loaders.TestDataLoadersAndAnalysis.test_secodeplt_loader) ... ok
test_cross_split_deduplicator (test_preprocessing.TestPreprocessing.test_cross_split_deduplicator) ... ok
test_pipeline_end_to_end (test_preprocessing.TestPreprocessing.test_pipeline_end_to_end) ... ok
test_prepare_for_classical_and_codebert (test_preprocessing.TestPreprocessing.test_prepare_for_classical_and_codebert) ... ok
test_safe_comment_remover_preserves_urls_and_strings (test_preprocessing.TestPreprocessing.test_safe_comment_remover_preserves_urls_and_strings) ... ok
test_token_length_distribution_percentiles (test_preprocessing.TestPreprocessing.test_token_length_distribution_percentiles) ... ok
test_untruncated_token_lengths (test_preprocessing.TestPreprocessing.test_untruncated_token_lengths) ... ok

----------------------------------------------------------------------
Ran 40 tests in 0.203s

OK (skipped=3)
```

**Results:**
- **Total Tests:** 40
- **Passed:** 37
- **Failed:** 0
- **Skipped:** 3 (PyTorch-dependent tests safely skipped in local CPU Python environment)

### Frontend Production Build:
```bash
cd frontend && npm run build
```
- **Result:** `tsc -b && vite build` completed in 1.50s with **0 errors and 0 warnings**.

---

## 5. Files Changed Summary

1. **[.gitignore](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/.gitignore):** Added `datasets/raw/*` and `datasets/processed/*` patterns while unignoring tracked JSONL files. Fixed failing unit test.
2. **[backend/app/schemas/scan.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/schemas/scan.py):** Added `allow_fallback`, `requested_model`, `actual_model`, and `fallback_used` fields.
3. **[backend/app/services/model_service.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/backend/app/services/model_service.py):** Removed artificial CodeBERT probability simulation. Implemented explicit 503 when PyTorch runtime is missing and transparent fallback attribution.
4. **[tests/test_api.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/tests/test_api.py):** Added unit tests verifying model attribution, explicit 503 status, and transparent fallback behavior.
5. **[frontend/src/types/api.ts](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/frontend/src/types/api.ts):** Synchronized TypeScript API contracts with backend schemas.
6. **[frontend/src/components/ScannerTab.tsx](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/frontend/src/components/ScannerTab.tsx):** Added fallback notice banner and updated dropdown status text.
7. **[scripts/run_cross_evaluation.py](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/scripts/run_cross_evaluation.py):** Updated report generator to distinguish smoke tests from full-scale benchmarks and display $N$ counts.
8. **[datasets/reports/CROSS_DATASET_EVALUATION_REPORT.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/datasets/reports/CROSS_DATASET_EVALUATION_REPORT.md):** Updated markdown report to clearly annotate smoke tests, incomplete experiments, and cohort sizes.
9. **[docs/RESEARCH_REMEDIATION_LOG.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_REMEDIATION_LOG.md):** Created this comprehensive audit and remediation record.

---

## 6. Remaining Issues & Next Phase Strategy

1. **Local PyTorch Runtime:**
   * PyTorch is not installed in the Windows Python 3.13 environment.
   * *Status:* Safe transparent fallback is now active. If local PyTorch execution is desired, Python 3.11 with matching PyTorch wheels should be installed in a dedicated `.venv`.
2. **Dataset Scale Expansion (Phase 2):**
   * The local repository contains curated 16-sample smoke-test partitions.
   * To transition to research-grade benchmarks without burdening local disk or CPU, the Google Colab notebook ([notebooks/01_codebert_finetuning.ipynb](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/notebooks/01_codebert_finetuning.ipynb)) will be augmented in Phase 2 with a cell to download full CodeXGLUE and LLMVul sets directly onto Colab GPU runtimes.
3. **Paper Revision (Phase 2):**
   * The unsupported claims identified in Section 3 will be updated in [docs/RESEARCH_PAPER.md](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md) once the user approves the remediation log.

*Confirmation: No experimental results were fabricated, altered, or overwritten.*
