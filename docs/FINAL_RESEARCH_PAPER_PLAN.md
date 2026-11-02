# SecureCode AI — Final Research Paper & Deliverables Implementation Plan

**Date:** November 2026  
**Document ID:** `docs/FINAL_RESEARCH_PAPER_PLAN.md`  
**Status:** Approved for Execution  
**Target Venue / Submission:** Academic Conference / IEEE/ACM Workshop Track  
**Repository:** [https://github.com/0Tusharbhardwaj/nlp](https://github.com/0Tusharbhardwaj/nlp)

---

## 1. Executive Summary & Scope Reframing (Professor's Guidance)

### Critical Scope Correction
> **Academic Feedback:** Remove all broad claims of "checking entire security" or "guaranteeing system security." Security encompasses network perimeters, cryptography, dynamic authorization, access control, and runtime defense-in-depth. 
> 
> **Reframed Scientific Scope:** The research paper focuses strictly and exclusively on **Static Source Code Vulnerability Detection** (specifically function-level binary classification of Common Weakness Enumerations including CWE-120 buffer overflows, CWE-78 command injection, and CWE-415 memory flaws) and investigating the **Domain Generalization Gap** between human-authored and LLM-generated software.

### Approved Paper Titles
* **Primary Title:** *Investigating the Domain Generalization Gap in Neural Vulnerability Detection: From Human-Authored to LLM-Generated Source Code*
* **Alternative Title:** *Cross-Domain Transferability of Neural Code Classifiers: An Empirical Evaluation Across Human and AI-Generated C Benchmarks*

---

## 2. Core Scientific Finding (What We Aimed For & Discovered)

```
                       [Human C Code (Devign)]
                                  │
                                  ▼
               CodeBERT In-Distribution Performance (E1)
                    Accuracy: 66.36% | Macro F1: 64.71%
                    ROC-AUC: 0.7301  | Precision: 68.96%
                                  │
                                  │ Zero-Shot Transfer
                                  │ to LLM-Generated Code
                                  ▼
                  AI Code Zero-Shot Evaluation (E2)
                   (LLMVul 8 Disjoint Repositories)
                    Accuracy: 8.93%  | Macro F1: 8.23%
                    Domain Collapse: Δ Macro F1 = -56.48%
```

### The 3 Anchor Findings of the Paper:
1. **The Domain Shift Collapse ($\Delta \text{Macro F1} = -56.48\%$):**
   When a transformer model (CodeBERT) fine-tuned exclusively on human-written open-source code (Devign) is evaluated zero-shot on LLM-generated code (LLMVul), its performance collapses. Because LLMs introduce distinct stylistic artifacts, verbose identifiers, and synthetic syntactic regularities, the classifier misinterprets benign LLM code as vulnerable, driving accuracy down to 8.93%.
2. **Benchmark Artifacts & Repository Leakage in Devign:**
   Our empirical audit of the official CodeXGLUE / Devign benchmark revealed that its test split shares **100% of repositories** (`qemu` and `FFmpeg`) with the training split, alongside 10 identical duplicate functions and 57 contradictory labels. Standard benchmark numbers in the literature are inflated by repository memorization.
3. **Zero-Shot Failure on CVE Ground-Truth Patches (SeCodePLT):**
   When evaluated on 2,480 balanced pairs of CVE-vulnerable functions and their verified patches, zero-shot models achieve **50.00% accuracy** and **0.4993 ROC-AUC** (equivalent to random guessing), demonstrating that sequence-level models cannot distinguish subtle patch-level security deltas without contrastive training.

---

## 3. Empirical Data Master Matrix (To Be Embedded in Paper)

All numbers are grounded directly in our verified full-scale Colab GPU runs:

| Experiment Setting | Training Cohort | Evaluation Cohort | Sample Count ($N$) | Accuracy | Macro F1 | Recall | FNR ($1 - \text{Recall}$) | ROC-AUC |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline 1 (LR)** | Devign Train | Devign Test | 2,732 | **61.35%** | **61.30%** | 62.79% | 37.21% | 0.6734 |
| **Baseline 2 (SVM)** | Devign Train | Devign Test | 2,732 | **59.44%** | **58.48%** | 48.13% | 51.87% | 0.6634 |
| **E1 (In-Distribution)** | Devign Train | Devign Test (Human) | 2,732 | **66.36%** | **64.71%** | 48.69% | 51.31% | **0.7301** |
| **E2 (Zero-Shot AI)** | Devign Train | LLMVul Holdout (8 Repos) | 4,120 | **8.93%** | **8.23%** | 100.0% | 0.00% | 0.6888 |
| **Gold Standard** | Devign Train | Expert Consensus AI | 85 | **97.65%** | 49.40% | 100.0% | 0.00% | 0.3675 |
| **SeCodePLT Transfer** | Devign Train | Balanced CVE Pairs | 2,480 | **50.00%** | 33.48% | 99.84% | 0.16% | 0.4993 |

*Metric Delta (Domain Shift):* $\Delta \text{Macro F1} = -56.48\%$ | $\Delta \text{FNR} = -51.31\%$

---

## 4. Section-by-Section Research Paper Drafting Plan

### Section 1: Abstract & Introduction
* **Core Problem:** The rapid adoption of generative AI tools (GitHub Copilot, Claude Code, ChatGPT) in software engineering.
* **The Research Gap:** Prior vulnerability detection benchmarks (Devign, Big-Vul, DiverseVul) rely almost exclusively on human open-source repositories. It is unproven whether neural representations trained on human code generalize to AI code.
* **Scope Boundary (Per Professor):** Explicit statement that this paper evaluates *static function-level vulnerability detection*, which is one component of software assurance and does not replace dynamic analysis, formal verification, or whole-system security.
* **Research Questions:**
  * **RQ1:** How do classical lexical baselines (TF-IDF with Logistic Regression and Calibrated Linear SVM) compare against deep pretrained contextual models (CodeBERT) on human C benchmarks?
  * **RQ2:** To what extent does a neural vulnerability classifier trained on human code transfer to AI-generated code under strict zero-leakage conditions?
  * **RQ3:** Does zero-shot vulnerability classification transfer to real-world CVE patch pairs (SeCodePLT)?

### Section 2: Related Work
* **Classical Static Analysis vs. ML:** AST-based rule matchers (Flawfinder, Cppcheck) vs. statistical NLP models.
* **Pretrained Models for Code:** RoBERTa, CodeBERT, GraphCodeBERT, and their contextual token embeddings.
* **Audits of AI-Generated Code:** Recent empirical studies (Pearce et al., Farhad & Dass 2024) revealing high vulnerability incidence in LLM code generation.

### Section 3: Benchmark Datasets & Data Hygiene Audit
* **Dataset A (CodeXGLUE/Devign):** 27,318 C functions (21,854 train / 2,732 val / 2,732 test). Document the 100% repository overlap finding.
* **Dataset B (LLMVul):** 21,430 AI-generated functions across 226 production GitHub repositories. Quarantine of 2,679 ambiguous labels.
* **Repository-Disjoint Partitioning:** Algorithmic isolation of 8 holdout repositories (0% repository leakage).
* **Dataset C (SeCodePLT):** Standalone adapter generating 2,480 balanced pairs (1 vulnerable, 1 patch) for CVE transfer testing.
* **Syntax-Preserving Preprocessing:** 5-state lexer state machine preserving string URLs and multiline structure while stripping comments.

### Section 4: Modeling Methodology
* **Lexical Baselines:** TF-IDF n-grams $(1, 2)$ with sublinear scaling, operator tokens, and balanced class weights.
* **Calibrated Linear SVM:** Platt sigmoid scaling mapping unbounded SVM hyperplane distances $w^T x + b$ into continuous probabilities.
* **CodeBERT Sequence Classifier:** Bimodal RoBERTa backbone (12 layers, 768 hidden, 12 heads, 125M parameters) + custom classification head.
* **Colab GPU Training Protocol:** Tesla T4 GPU, FP16 mixed precision, AdamW ($\text{lr} = 2 \times 10^{-5}$), cosine decay, 341 dynamic warmup steps, 3 epochs on 21,854 samples.

### Section 5: Experimental Evaluation & Results
* **RQ1 Results (Human In-Distribution):** CodeBERT (64.71% F1) beats Logistic Regression (61.30% F1) and SVM (58.48% F1) with 0.7301 ROC-AUC.
* **RQ2 Results (AI Transfer Collapse):** Empirical quantification of the $-56.48\%$ drop in Macro F1 and analysis of false-positive surges on AI code.
* **RQ3 Results (CVE Patch Transfer):** Analysis of SeCodePLT's 50.00% random-guess level and why token-level models miss surgical security patches.
* **Side-by-Side Confusion Matrices:** Embedding `results/figures/cross_dataset_e1_vs_e2_cm.png` and `baselines_devign_test_cm.png`.

### Section 6: Threats to Validity
* **Construct Validity:** 512-token truncation policy (audited 23.12% truncation rate in Devign).
* **Internal Validity:** Absence of cross-dataset repository contamination guaranteed by disjoint partitioning.
* **External Validity:** Generalization to non-C languages (Java, Python) requires distinct AST tokenizers.

### Section 7: System Implementation & Artifact Availability
* **FastAPI Backend:** Sub-15ms inference latency, transparent model attribution (`requested_model`, `actual_model`, `fallback_used`).
* **Web Dashboard:** Interactive Monaco Editor C/C++ scanner, Recharts visualizer, and live telemetry.
* **Reproducibility:** GitHub repository, open checkpoints (`model.safetensors`), and automated Colab notebooks (`02`, `03`, `04`).

### Section 8: Conclusion
* Summary of findings, recommendation against naive deployment of human-trained classifiers on AI pipelines, and future directions for domain-adapted vulnerability detection.

---

## 5. File Cleanup & Maintenance Log

The following obsolete, temporary, and toy smoke-test files have been deleted from the repository:
1. `notebooks/01_codebert_finetuning.ipynb` (Old 4-sample toy smoke test notebook, superseded by notebooks 02, 03, 04).
2. `scripts/verify_frontend_ui.py` (Temporary testing script).
3. `results/figures/ui_*.png` (Temporary debug screenshots).
4. `results/models/tfidf_linear_svm.joblib` (Old 2KB smoke-test model, superseded by `linear_svm_full.joblib`).
5. `results/models/tfidf_logistic_regression.joblib` (Old 2KB smoke-test model, superseded by `logistic_regression_full.joblib`).

*Preserved Full-Scale Production Artifacts:*
- `results/models/codebert_devign_full/` (Full 498MB `model.safetensors` trained on 21,854 Devign functions).
- `results/models/linear_svm_full.joblib` (Full 1.2MB calibrated baseline).
- `results/models/logistic_regression_full.joblib` (Full 400KB baseline).
- `results/models/tfidf_vectorizer_full.joblib` (Full 2.0MB TF-IDF vectorizer).
- `results/metrics/full_scale_baselines_metrics.json` & `cross_dataset_full_scale_results.json` (Real Colab evaluation numbers).

---

## 6. Execution Steps & Deliverables

| Step | Action Item | Target File | Output / Deliverable |
| :---: | :--- | :--- | :--- |
| **1** | Rewrite research paper in Markdown with scoped terminology and real metrics | [`docs/RESEARCH_PAPER.md`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md) | Publication-ready paper draft |
| **2** | Generate Overleaf / LaTeX template file for IEEE/ACM conference format | `docs/paper/main.tex` | PDF-compilable LaTeX file |
| **3** | Update system documentation and architecture docs to match scoped terminology | [`README.md`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/README.md), [`docs/PROJECT_ARCHITECTURE.md`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/PROJECT_ARCHITECTURE.md) | Synchronized repository documentation |
| **4** | Commit and push all cleaned files and updated paper to GitHub | Git repository (`origin/main`) | Synced remote repository |

