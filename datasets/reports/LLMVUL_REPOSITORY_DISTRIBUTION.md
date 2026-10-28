# SecureCode AI — LLMVul Repository Partition & Distribution Audit

**Generated:** 2026-10-28  
**Audit Scope:** Deep audit of LLMVul repository-disjoint partitioning (Train vs Holdout).  
**Status:** Preserved as Partition V1 (`llmvul_split_v1`); Alternative Partition V2 Proposed.

---

## 1. Executive Summary

To prevent optimistic data leakage in cross-domain vulnerability detection, LLMVul was partitioned at the **repository boundary** rather than randomly across functions. This ensures that no code from any training repository appears in the holdout evaluation partition:

$$\text{Train Repositories} \cap \text{Holdout Repositories} = \emptyset$$

This audit examines the eight repositories comprising the 4,120-sample holdout partition, measures per-repository vulnerability rates, analyzes repository dominance and selection bias introduced by the greedy partitioner, and proposes a stratified alternative partition as a separate future experiment.

---

## 2. Holdout Partition Repository Breakdown (8 Disjoint Repositories)

| Repository Identifier | Primary Language / Domain | Total Functions | Safe Functions (0) | Vulnerable Functions (1) | Vulnerability Rate (%) | Share of Holdout Functions (%) | Share of Holdout Vulnerabilities (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`nature-lang/nature`** | Programming Language / Compiler | 934 | 707 | 227 | **24.30%** | **22.67%** | **62.36%** |
| **`microsoft/ebpf-for-windows`** | Kernel / eBPF Networking | 689 | 662 | 27 | 3.92% | 16.72% | 7.42% |
| **`isl-org/Open3D`** | 3D Data Processing & Graphics | 429 | 407 | 22 | 5.13% | 10.41% | 6.04% |
| **`microsoft/onnxruntime`** | Machine Learning Inference Engine | 426 | 410 | 16 | 3.76% | 10.34% | 4.40% |
| **`carla-simulator/carla`** | Autonomous Driving Simulation | 422 | 417 | 5 | 1.18% | 10.24% | 1.37% |
| **`DarkFlippers/unleashed-firmware`** | Embedded Hardware / Firmware | 413 | 376 | 37 | 8.96% | 10.02% | 10.16% |
| **`DavidXanatos/TaskExplorer`** | Windows Process Explorer / Tool | 406 | 377 | 29 | 7.14% | 9.85% | 7.97% |
| **`microsoft/WSL`** | Windows Subsystem for Linux | 401 | 400 | 1 | 0.25% | 9.73% | 0.27% |
| **Total Holdout Partition** | **8 Disjoint Repositories** | **4,120** | **3,756** | **364** | **8.83%** | **100.0%** | **100.0%** |

---

## 3. Critical Concentration & Selection Bias Analysis

### 3.1. Dominance of `nature-lang/nature`
- **Vulnerability Concentration:** `nature-lang/nature` accounts for **227 out of the 364 total vulnerabilities in the holdout partition (62.36%)**.
- **Domain Characteristic:** `nature` is an experimental programming language compiler. Compiler codebases frequently contain recursive AST transformations, parser loops, and raw pointer memory management that exhibit significantly higher static analyzer finding density (24.30%) compared to enterprise systems code (1% to 5%).
- **Evaluation Impact:** Any model's recall or false negative rate on the LLMVul holdout set will be disproportionately driven by its ability to detect compiler/runtime bugs in `nature-lang/nature`.

### 3.2. Dominance of Microsoft Corporate Repositories
- Three of the eight holdout repositories originate from Microsoft organizations:
  - `microsoft/ebpf-for-windows` (689 samples)
  - `microsoft/onnxruntime` (426 samples)
  - `microsoft/WSL` (401 samples)
- **Combined Microsoft Volume:** $689 + 426 + 401 = 1,516$ functions (**36.80% of the entire holdout partition**).
- **Stylistic Implication:** Microsoft codebases adhere to strict SAL (Source Code Annotation Language), `wil` (Windows Implementation Libraries), and modern C++ guidelines. This introduces an organizational coding style concentration.

### 3.3. Top-Heavy Concentration
- Together, `nature-lang/nature` and the three Microsoft repositories represent:
  - **2,450 out of 4,120 functions (59.47%)** of all holdout samples.
  - **271 out of 364 vulnerabilities (74.45%)** of all holdout vulnerabilities.

### 3.4. Mechanics of the Greedy Partitioning Algorithm
The greedy partitioner in `src/data/llmvul_partitioner.py` sorted repositories by size descending (`n_funcs`), then allocated projects into the holdout until the 20% sample budget (approx. 4,000 functions) was filled.
- The largest repository in LLMVul (`Serial-Studio/Serial-Studio`, 5,462 functions) was assigned to Train because it exceeded the single-project size budget ($22\% \approx 4,125$ samples).
- The next tier of large repositories (400 to 950 functions each) was sequentially allocated to Test.
- **Selection Bias:** This algorithm systematically selected mid-to-large repositories for holdout while populating the training set with 216 repositories (including 180+ small repositories with fewer than 100 functions).

---

## 4. Disjointness Verification

Programmatic verification was executed across the partition metadata:
```python
train_repos = set(meta["train_repos"]) # 216 repositories
test_repos = set(meta["test_repos"])   # 8 repositories
assert len(train_repos & test_repos) == 0
```
- **Shared Repositories:** Exactly **0** (0.0%).
- **Verification Result:** PASS. Zero repository leakage between training and evaluation partitions.

---

## 5. Preservation Policy & Proposed Alternative Partition (Experiment V2)

### 5.1. Preservation Policy
In accordance with scientific reproducibility standards, **the current partition V1 (`llmvul_train_clean.jsonl`, `llmvul_test_clean.jsonl`) will NOT be silently replaced or modified**. All primary Phase 2 baseline and CodeBERT evaluations will execute on this preserved partition, with its dominance characteristics transparently documented.

### 5.2. Proposed Alternative Experiment: Stratified Size-Bin Partition (Partition V2)
As a separate, comparative sensitivity analysis, we propose an alternative partition strategy:
1. Stratify the 226 repositories into four size quartiles (Large $>300$, Medium $100-300$, Small $25-100$, Micro $<25$).
2. Sample repositories proportionally from each quartile using stratified hash partitioning.
3. Cap any single repository at a maximum of 15% of the holdout vulnerability total to prevent single-codebase dominance.

| Dimension | Partition V1 (Current - Preserved) | Proposed Partition V2 (Sensitivity Cohort) |
| :--- | :--- | :--- |
| **Holdout Repositories** | 8 repositories | 35–45 repositories |
| **Max Repo Function Share** | 22.67% (`nature-lang/nature`) | $\le 10.0\%$ |
| **Max Repo Vulnerability Share**| **62.36%** (`nature-lang/nature`) | $\le 15.0\%$ |
| **Domain Diversity** | 5 distinct domains | 18+ distinct domains |
| **Disjointness Guarantee** | 100% Disjoint | 100% Disjoint |
