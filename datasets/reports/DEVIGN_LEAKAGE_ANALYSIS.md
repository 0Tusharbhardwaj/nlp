# SecureCode AI — Devign Leakage & Label Contradiction Audit

**Generated:** 2026-10-28  
**Audit Scope:** Deep audit of CodeXGLUE / Devign benchmark split overlap, exact function duplicates, and label contradictions.  
**Benchmark Reference:** Microsoft CodeXGLUE defect detection / Zhou et al. (NeurIPS 2019).

---

## 1. Executive Summary

The **CodeXGLUE / Devign** defect detection benchmark consists of 27,318 C functions extracted from two major open-source projects: **QEMU** and **FFmpeg**. This audit inspects the official partition counts, examines 10 exact duplicate functions crossing the train-test boundary, analyzes 57 label contradictions within the training set, explains their root cause, and proposes a separate deduplicated sensitivity benchmark without altering the official evaluation splits.

---

## 2. Official Split Verification

| Partition Name | Verified Sample Count | Share of Benchmark | Vulnerable (1) | Safe (0) | Vulnerability Rate | Missing Values |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train Split** | **21,854** | 79.998% | 10,018 | 11,836 | 45.84% | 0 (0.0%) |
| **Validation Split** | **2,732** | 10.001% | 1,187 | 1,545 | 43.45% | 0 (0.0%) |
| **Test Split** | **2,732** | 10.001% | 1,255 | 1,477 | 45.94% | 0 (0.0%) |
| **Total Devign Benchmark** | **27,318** | **100.0%** | **12,460** | **14,858** | **45.61%** | **0 (0.0%)** |

---

## 3. Audit of the 10 Exact Train-Test Duplicate Functions

Character-for-character exact duplicate audit (after whitespace normalization) identified **10 function hashes** that appear in both the training split and the official test split.

| # | Code Hash (SHA256 Prefix) | Function Identifier / Signature | Project | Train ID(s) | Train Label | Test ID(s) | Test Label | Label Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `0fc9bfd7505e` | `av_parse_color(...)` | FFmpeg | 21509 | **1 (Vuln)** | 16256 | **0 (Safe)** | **CONTRADICTORY** |
| **2** | `39100173ed2e` | `theora_gptopts(...)` | FFmpeg | 9606 | **1 (Vuln)** | 23159 | **0 (Safe)** | **CONTRADICTORY** |
| **3** | `0196b95a8309` | `kvm_client_migration_log(...)` | QEMU | 27172 | **1 (Vuln)** | 14476 | **0 (Safe)** | **CONTRADICTORY** |
| **4** | `53bcbddcea1e` | `kvm_client_sync_dirty_bitmap(...)` | QEMU | 8753 | **0 (Safe)** | 21511 | **1 (Vuln)** | **CONTRADICTORY** |
| **5** | `9591403bd550` | `output_frame(...)` | FFmpeg | 6623 | **0 (Safe)** | 5908 | **1 (Vuln)** | **CONTRADICTORY** |
| **6** | `7893fcbae88f` | `kvm_physical_sync_dirty_bitmap(...)`| QEMU | 12467 | **0 (Safe)** | 1473 | **1 (Vuln)** | **CONTRADICTORY** |
| **7** | `fae35c9a54cd` | `bdrv_pread(...)` | QEMU | 19594 | **1 (Vuln)** | 9176 | **1 (Vuln)** | **MATCHING (Leakage)** |
| **8** | `cd707755dc9e` | `add_bytes_l2_c(...)` | FFmpeg | 26622 | **0 (Safe)** | 18624 | **1 (Vuln)** | **CONTRADICTORY** |
| **9** | `6355c1946350` | `decode_mb_info(...)` | FFmpeg | 8708 | **1 (Vuln)** | 9162 | **1 (Vuln)** | **MATCHING (Leakage)** |
| **10**| `07cb4e6b659c` | `parse_header(...)` | FFmpeg | 4852 | **1 (Vuln)** | 11553 | **0 (Safe)** | **CONTRADICTORY** |

### Key Discovery: Contradiction Dominance
- Out of the 10 cross-split duplicates, **8 out of 10 (80.0%) exhibit contradictory ground-truth labels** between Train and Test!
- Only 2 functions (`bdrv_pread` and `decode_mb_info`) share the same label (vulnerable) in both splits.

---

## 4. Audit of 57 Contradictory Duplicate Labels within the Training Split

Within the training set alone (`train.parquet`), **57 unique function bodies appear multiple times with mutually conflicting labels** ($y=0$ and $y=1$ on the identical code).

### Representative Contradiction Examples
1. **`ff_ivi_decode_blocks(...)` (FFmpeg):**
   - ID 817 is labeled **0 (Safe)**; ID 15755 is labeled **1 (Vulnerable)**.
2. **`pc_init1(...)` (QEMU):**
   - ID 839 is labeled **1 (Vulnerable)**; ID 12749 is labeled **0 (Safe)**.
3. **`cin_decode_rle(...)` (FFmpeg):**
   - ID 922 is labeled **1 (Vulnerable)**; ID 21140 is labeled **0 (Safe)**.
4. **`arm_v7m_load_vector(...)` (QEMU):**
   - ID 955 is labeled **1 (Vulnerable)**; ID 3835 is labeled **0 (Safe)**.
5. **`uninit(...)` (FFmpeg):**
   - ID 1272 is labeled **0 (Safe)**; ID 14752 is labeled **1 (Vulnerable)** (`static void uninit(struct vf_instance *vf) { free(vf->priv); }`).

---

## 5. Root Cause Analysis: How Did This Enter the Benchmark?

The root cause stems from the automated mining methodology used to construct the Devign dataset:
1. **Commit-Level Slicing:** Zhou et al. (2019) mined Git commits classified as security fixes vs non-security commits.
2. **Co-Committed Unmodified Functions:** When a commit touched multiple functions in a source file, *all* functions present in that diff hunk or file were extracted and inherited the commit-level label.
3. **Multi-Commit Re-appearance:** A function that was not modified by the vulnerability fix was extracted as "vulnerable" in commit $C_1$, and later extracted as "safe" in a subsequent routine refactoring commit $C_2$. Because the function itself did not change, identical code strings received contradictory ground-truth labels.

### Research Implications for Model Training
1. **Gradient Interference:** For the 57 contradictory training functions, the cross-entropy loss generates opposing gradient vectors during backpropagation, injecting noise into the weight updates.
2. **Memorization Penalty:** If CodeBERT perfectly memorizes the training data, it will be penalized on 8 of the 10 duplicate test samples because the test set contains the inverted label.
3. **Accuracy Ceiling:** The presence of label noise establishes an empirical Bayes error rate that prevents any deterministic model from achieving 100% accuracy on Devign.

---

## 6. Proposed Sensitivity Analysis (Preserving Official Benchmark)

### 6.1. Preservation Rule
In strict adherence to scientific rigor, **the official CodeXGLUE / Devign benchmark splits will NOT be altered**. Primary evaluation in notebooks `02_full_scale_baselines.ipynb` and `03_codebert_full_scale_training.ipynb` must report numbers on the untouched official test set to ensure comparability with published literature.

### 6.2. Proposed Cleaned Sensitivity Cohort (`devign_clean_test`)
To measure the true impact of this label noise, we propose a supplementary sensitivity experiment:
1. Remove the 10 cross-split duplicates from the evaluation cohort.
2. Deduplicate training functions by taking the majority vote or removing contradictory pairs.
3. Compare model performance on:
   - Official Test Set: 2,732 samples.
   - Deduplicated Cleaned Test Set: 2,722 samples.
This establishes whether model errors on the official benchmark represent genuine generalization failures or benchmark label artifacts.
