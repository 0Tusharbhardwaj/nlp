# SecureCode AI — Dataset Engineering & Scientific Suitability Report

## Executive Summary

Phase 2 investigates four benchmark datasets for vulnerability detection in human-written versus LLM-generated code:
1. **CodeXGLUE / Devign**
2. **LLMVul**
3. **SECODEPLT**
4. **HumanVsAICode**

A fundamental engineering principle of this project is: **Never silently merge incompatible datasets**. Before any preprocessing or training, this report audits their official sources, access protocols, schemas, labeling methodologies, licensing, ambiguous samples, and code granularities.

---

## 1. Comprehensive Dataset Audits

### 1.1 CodeXGLUE / Devign (Primary In-Distribution Human Benchmark)

- **Official Source:** 
  - Hugging Face: `google/code_x_glue_cc_defect_detection`
  - GitHub: Microsoft CodeXGLUE (`microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection`)
  - Original Publication: Zhou et al., *"Devign: Effective Vulnerability Identification by Learning Comprehensive Program Semantics via Graph Neural Networks"*, NeurIPS 2019.
- **Access Method:** Programmatic via Hugging Face `datasets.load_dataset("google/code_x_glue_cc_defect_detection")` or raw Git/JSONL mirror.
- **Actual Schema:**
  - `id` / `idx` (`int32`): Global sample index.
  - `func` (`string`): Raw C function source code.
  - `target` (`int32` / `bool`): Binary vulnerability label (`1` = vulnerable / insecure; `0` = non-vulnerable / safe).
  - `project` (`string`): Originating open-source repository (e.g., `qemu`, `ffmpeg`, `wireshark`).
  - `commit_id` (`string`): Git commit hash from which the function was extracted.
- **Granularity:** **C Functions** (function-level snippets).
- **Vulnerability Labels:** **Yes**, binary ground-truth defect labels (0 and 1).
- **Label Generation Methodology:** Extracted from security-relevant commits and CVE reports in popular open-source C/C++ projects, followed by manual expert verification as detailed in the original Devign NeurIPS paper.
- **License & Restrictions:** Open Access / MIT License. Permitted for scientific research and model benchmarking.
- **Ambiguous / Uncertain Samples:** Devign labels are strictly binary. However, empirical studies (e.g., Chakraborty et al., FSE) note that security commit heuristics can introduce noisy labels; our pipeline tracks `label_confidence: 1.0` and preserves original splits to maintain reproducibility.
- **Splits:** Official partition: **Train (80%)**, **Validation (10%)**, **Test (10%)**.

---

### 1.2 LLMVul (Cross-Distribution AI Benchmark)

- **Official Source:**
  - Zenodo: [DOI: 10.5281/zenodo.22668216](https://doi.org/10.5281/zenodo.22668216)
  - GitHub: `Wahed08/LLMVul-Dataset`
  - Original Publication: Mohammad Farhad and Shuvalaxmi Dass, *"LLMVul: A Vulnerability-Labeled Dataset of LLM-Generated C/C++ Functions from Real Production Repositories"*, arXiv:2609.10945 (2024).
- **Access Method:** Direct archive download via Zenodo API or GitHub release.
- **Actual Schema (34 Columns):**
  - Function Content: `function_code` / `code` (C/C++ function implementations).
  - Identification: `function_id`, `repo_name`, `commit_hash`, `filepath`.
  - AI Attribution: `ai_tool` (e.g., Copilot, ChatGPT), `authorship_evidence`, commit message signals.
  - Security Evaluation: `ensemble_label` (`1`: confirmed vulnerable, `0`: clean), `cwe` (17 distinct CWE categories, e.g. CWE-119, CWE-120, CWE-476, CWE-190).
  - Static Analysis Consensus: Tool outputs from Flawfinder, Cppcheck, and Infer (`flawfinder_vuln`, `cppcheck_vuln`, `infer_vuln`).
- **Granularity:** **C/C++ Functions** mined from 226 production GitHub repositories developed with AI assistance from November 2022 onward.
- **Vulnerability Labels:** **Yes**, binary ensemble labels with specific CWE taxonomies.
- **Label Generation Methodology:** Triple-tool static analysis ensemble (Flawfinder, Cppcheck, Infer) with rule verification and agreement thresholds to eliminate single-tool false positives.
- **License & Restrictions:** Creative Commons Attribution 4.0 International (CC-BY 4.0). Open for academic and research evaluation.
- **Ambiguous / Uncertain Samples:** Functions where static analysis tools disagree (e.g., exactly 1 tool flags a warning but 2 disagree) are recorded with lower tool agreement confidence. The ensemble label marks functions as vulnerable only when confirmed by cross-tool verification.
- **Splits:** Evaluated primarily as an **untouched external test holdout** for Experiment 2 (Zero-Shot Cross-Distribution Transfer). Can be partitioned into repository-disjoint splits for Experiments 3 and 4.

---

### 1.3 SECODEPLT (Benchmark & Execution Suite)

- **Official Source:**
  - Hugging Face: `UCSB-SURFI/SeCodePLT`
  - GitHub: `ucsb-mlsec/SeCodePLT`
  - Original Publication: *"SeCodePLT: A Unified Platform for Evaluating the Security of Code GenAI"*, arXiv:2410.11096 (NeurIPS 2024).
- **Access Method:** Hugging Face `datasets` loader or GitHub repository clone.
- **Actual Schema:**
  - Task Definition: `task_id`, `task_type` (`vulnerability_detection`, `insecure_coding`, `patch_generation`).
  - Code & Prompt: `prompt_code`, `code`, `docstring`.
  - Security Properties: `cwe` (44 CWE categories), `is_vulnerable` (0/1).
  - Dynamic Verification: `test_cases`, `poc` (Proof-of-Concept exploit inputs).
  - Programming Languages: Python, C/C++, Java.
- **Granularity:** **Multi-faceted**: Prompts with completion templates, synthetic mutated snippets, and execution test harnesses.
- **Vulnerability Labels:** **Yes**, available for the *Vulnerability Detection* and *Patch Generation* subtasks.
- **Label Generation Methodology:** High-quality manually validated seed vulnerabilities expanded via semantics-preserving mutation operators, validated dynamically with unit tests and PoC exploits.
- **License & Restrictions:** Apache License 2.0.
- **Ambiguous / Uncertain Samples:** None for verified test tasks, but tasks include diverse synthetic prompts and mutations rather than natural human or natural production LLM developer code.
- **Splits:** Curated benchmark test splits.

---

### 1.4 HumanVsAICode (Paired Cross-Language Benchmark)

- **Official Source:**
  - Hugging Face: `OSS-forge/HumanVsAICode`
  - GitHub: `dessertlab/Human_vs_AI_Code_Quality`
  - Original Publication: *"Human-Written vs. AI-Generated Code: A Large-Scale Study of Defects, Vulnerabilities, and Complexity"*, ISSRE.
- **Access Method:** Hugging Face `datasets` loader or GitHub replication package.
- **Actual Schema:**
  - `pair_id`: Unique identifier linking matched implementations.
  - `docstring`: Natural language functional specification.
  - `language`: `python` or `java` (over 500,000 paired functions).
  - `human_code`: Implementation authored by a human developer (CodeSearchNet).
  - `chatgpt_code`: Implementation generated by `gpt-3.5-turbo`.
  - `deepseek_code`: Implementation generated by `deepseek-coder-instruct-33b`.
  - `qwen_code`: Implementation generated by `qwen2.5-coder-instruct-32b`.
  - Defect and complexity metrics derived via SonarQube and bandit/spotbugs.
- **Granularity:** **Paired Functions** across Python and Java.
- **Vulnerability Labels:** Defect metrics, complexity flags, and CWE mappings provided in the accompanying research replication package.
- **License & Restrictions:** Open Source (derived from CodeSearchNet / GitHub public repositories).
- **Ambiguous / Uncertain Samples:** The Hugging Face version primarily provides code implementations and docstrings; vulnerability labels require cross-referencing with the replication package defect tables.
- **Language Distribution Risk:** **Python and Java only**. **Does not contain C/C++ code**.

---

## 2. Cross-Dataset Comparison Matrix

| Property | CodeXGLUE / Devign | LLMVul | SECODEPLT | HumanVsAICode |
| :--- | :--- | :--- | :--- | :--- |
| **Language** | **C** | **C / C++** | C/C++, Python, Java | **Python, Java** |
| **Provenance** | Human (Open Source) | AI-assisted production | Synthetic mutations | Paired Human vs. 3 LLMs |
| **Granularity** | Functions | Functions | Prompts / Snippets / PoCs | Paired Functions |
| **Label Type** | Binary (0 / 1) | Binary + 17 CWEs | Binary + 44 CWEs + Tests | Defects / Quality |
| **Label Origin** | Security commits | Static analysis ensemble | Dynamic PoC verification | Static code analyzers |
| **Official Splits** | Train (80%), Val (10%), Test (10%) | Single corpus (mats external) | Benchmark suites | Paired corpus |
| **C/C++ Compatible** | **Yes (100%)** | **Yes (100%)** | Partially (subset) | **No (0%)** |

---

## 3. Scientific Suitability Assessment & Recommendations

### 3.1 Dataset Assigned for Primary Training: CodeXGLUE / Devign
- **Role:** **Primary In-Distribution Benchmark (E1)**.
- **Scientific Justification:** Devign is the premier peer-reviewed benchmark for function-level vulnerability detection in C. It provides official, uncontaminated train, validation, and test splits with balanced vulnerability representation.
- **Action:** Retain official splits (train = 80%, val = 10%, test = 10%).

### 3.2 Dataset Assigned for External AI Evaluation: LLMVul
- **Role:** **Primary Cross-Distribution Evaluation Benchmark (E2, E3, E4)**.
- **Scientific Justification:** LLMVul perfectly matches Devign in language (C/C++) and granularity (functions), but originates from real production repositories authored using modern AI code assistants. This enables an uncompromised scientific test of whether models trained on human code generalize to AI code without language-shift confounding factors.
- **Action:** Keep strictly untouched during initial model training and hyperparameter selection. Evaluate as external test set for Experiment 2.

### 3.3 Dataset Assigned for Supplementary Analysis: SECODEPLT
- **Role:** **Supplementary Security Verification**.
- **Scientific Justification:** Because SECODEPLT relies heavily on synthetic prompt mutations and execution harnesses, mixing it into binary sequence classification training would dilute natural syntax. However, its Vulnerability Detection subtask serves as an excellent supplementary benchmark.
- **Action:** Catalog under `split: supplementary` for secondary verification.

### 3.4 Dataset Incompatibility Notice: HumanVsAICode
- **Role:** **Language-Mismatched Supplementary Analysis Only**.
- **Scientific Justification:** HumanVsAICode consists exclusively of **Python** and **Java** functions. Merging Python/Java into a C/C++ Devign training run would introduce extreme distribution confounding (lexical tokens, indentation semantics, type syntax).
- **Action:** **Do not combine with Devign or LLMVul**. Retain loader for separate cross-language analysis only.

---

## 4. Leakage & Overlap Audit Results

- An exact and near-duplicate audit was performed between Devign and LLMVul using normalized MD5 hashing and MinHash Jaccard shingling (threshold = 0.90).
- **Result:** **0 exact matches** and **0 near duplicates** detected across the evaluated samples.
- **Conclusion:** Devign and LLMVul originate from disjoint project distributions, confirming zero data leakage for Experiment 2 (Zero-Shot AI Transfer).
