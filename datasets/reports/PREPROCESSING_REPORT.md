# SecureCode AI — Data Preprocessing & Token-Length Audit Report

## 1. Executive Summary

This report documents the preprocessing results across evaluated vulnerability benchmarks.
Crucially, **token lengths are calculated on complete, untruncated code samples** before
applying any sequence bounds, allowing precise quantification of truncation exposure.

---

## 2. Token-Length Distribution & Truncation Audit (>512 Tokens)

| Dataset | Total Samples | Min | Max | Mean | Median | P90 | P95 | P99 | Exceeding 512 (%) | Exceeding 256 (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEVIGN** | 8 | 44 | 94 | 58.88 | 55.5 | 73.7 | 83.85 | 91.97 | **0.0%** | 0.0% |
| **LLMVUL** | 4 | 54 | 61 | 58.75 | 60.0 | 61.0 | 61.0 | 61.0 | **0.0%** | 0.0% |
| **SECODEPLT** | 4 | 31 | 54 | 44.5 | 46.5 | 53.4 | 53.7 | 53.94 | **0.0%** | 0.0% |

---

## 3. Cross-Split Leakage & Deduplication Audit

### Dataset: `DEVIGN`
- **Total Exact Cross-Split Leaks:** 0
  - `train_vs_valid`: CLEAN (0 leaks)
  - `train_vs_test`: CLEAN (0 leaks)
  - `valid_vs_test`: CLEAN (0 leaks)

### Dataset: `LLMVUL`
- **Total Exact Cross-Split Leaks:** 0
  - *Single external partition; cross-split comparison not applicable.*

### Dataset: `SECODEPLT`
- **Total Exact Cross-Split Leaks:** 0
  - *Single external partition; cross-split comparison not applicable.*

---

## 4. Preprocessed Partitions Summary

| Dataset | Partitions Saved | Storage Location |
| :--- | :--- | :--- |
| `devign` | train (4), valid (2), test (2) | `datasets/processed/devign/` |
| `llmvul` | external (4) | `datasets/processed/llmvul/` |
| `secodeplt` | supplementary (4) | `datasets/processed/secodeplt/` |
