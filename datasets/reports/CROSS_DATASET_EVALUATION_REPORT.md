# SecureCode AI — Cross-Dataset Evaluation & Generalization Report

## 1. Executive Summary & Experiment Integrity Classification

This empirical evaluation audits vulnerability detection models trained on historical human-written code (Devign)
against AI-generated and AI-assisted C/C++ code (LLMVul).

### Experiment Maturity & Status Breakdown:
| Category | Experiments | Scope & Description |
| :--- | :--- | :--- |
| **Completed Experiments (Full Scale)** | *None* | Awaiting full-scale multi-gigabyte dataset execution on GPU cluster / Google Colab. |
| **Smoke Tests (Pipeline Verification)** | **E1, E2, E3** | Local pipeline validation on curated function cohorts ($N=2$ to $4$ test samples). Validates zero vectorizer leakage, comment stripping, and metric computation mechanics. |
| **Incomplete Experiments** | **E4 (AI-Native)** | Skipped due to 1-sample class collapse ($N_{train}=1$, label=1; 0 safe samples). Requires multi-repository stratified cohort. |
| **Experiments Awaiting Full Scale** | **E1–E4 (Full Benchmarks)** | Full-scale training on complete CodeXGLUE (27,318 functions) and LLMVul (226 repositories) on high-memory GPU runtimes. |

### Key Empirical Findings on Smoke-Test Cohort:
1. **E1 Human In-Distribution**: Models predicted 100% of test samples as vulnerable (degenerate positive predictor), yielding 100% recall but 50% accuracy on balanced test set ($N=2$).
2. **E2 Zero-Shot AI Transfer**: Achieved 100% accuracy and 0.0% FNR across $N=4$ AI test samples. These high metrics are small-sample evaluation artifacts rather than proof of generalized AI security.
3. **E3 Joint Adaptation**: Retained 100% accuracy across $N=3$ repository-disjoint AI test samples.
4. **E4 AI-Native Baseline**: Incomplete due to single-class repository partition in the local smoke-test cohort.

---

## 2. Experimental Results Summary Table

| Experiment | Model | Classification | Train $N$ | Test $N$ | Accuracy | Precision | Recall | F1-Score | False Negative Rate (FNR) | ROC-AUC |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **E1_Human_In_Distribution** | Logistic Regression | **Smoke Test** | 4 | 2 | 0.5000 | 0.5000 | 1.0000 | **0.6667** | **0.0000** | 1.0 |
| **E1_Human_In_Distribution** | Linear SVM | **Smoke Test** | 4 | 2 | 0.5000 | 0.5000 | 1.0000 | **0.6667** | **0.0000** | 1.0 |
| **E2_ZeroShot_AI_Transfer** | Logistic Regression | **Smoke Test** | 4 | 4 | 1.0000 | 1.0000 | 1.0000 | **1.0000** | **0.0000** | 1.0 |
| **E2_ZeroShot_AI_Transfer** | Linear SVM | **Smoke Test** | 4 | 4 | 1.0000 | 1.0000 | 1.0000 | **1.0000** | **0.0000** | 1.0 |
| **E3_Joint_Adaptation** | Logistic Regression | **Smoke Test** | 5 | 3 | 1.0000 | 1.0000 | 1.0000 | **1.0000** | **0.0000** | 1.0 |
| **E3_Joint_Adaptation** | Linear SVM | **Smoke Test** | 5 | 3 | 1.0000 | 1.0000 | 1.0000 | **1.0000** | **0.0000** | 1.0 |
| **E4_AI_Native** | *All Models* | **Incomplete / Awaiting Full Data** | 1 | 3 | — | — | — | — | — | *Skipped (insufficient class diversity)* |

---

## 3. False Negative Vulnerability Analysis (Missed Flaws in AI Code)

The table below details specific vulnerabilities in AI-generated code that escaped human-trained detection during Experiment E2:

| Sample ID | CWE Category | Provenance / AI Tool | Repository | Snippet Excerpt |
| :--- | :--- | :--- | :--- | :--- |
| *No false negatives observed in evaluated test subset* | | | | |

---

## 4. Uncertain & Ambiguous Samples Audit

- **Total Samples with Ambiguous / Partial Consensus:** 0
- **Policy:** Uncertain labels are strictly quarantined from primary binary metrics to ensure zero noise contamination.

---

## 5. Scope & Language Generalization Limitations

> [!WARNING]
> **Language Generalization Disclaimer:**
> All findings, metrics, and models in this study are derived strictly from **C and C++** benchmarks.
> It is scientifically invalid to claim that these models generalize to memory-managed languages such as **Python, Java, or JavaScript**.
> Language-specific defect mechanics (e.g., buffer overflows in C vs. prototype pollution in JavaScript) require separate language-specific evaluations.
