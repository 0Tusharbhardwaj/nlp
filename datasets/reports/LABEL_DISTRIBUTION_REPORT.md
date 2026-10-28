# SecureCode AI — Label Distribution and Class Balance Report

**Generated:** 2026-10-28 12:48:57 UTC

---

## 1. Summary of Label Distributions Across Cohorts

| Benchmark Cohort | Partition | Safe (0) | Vulnerable (1) | Uncertain | Total Evaluated | Vulnerability Rate (%) | Class Ratio (Safe:Vuln) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Devign (Dataset A)** | Train | 11,836 | 10,018 | 0 | 21,854 | 45.84% | 1.18 : 1 |
| **Devign (Dataset A)** | Validation | 1,545 | 1,187 | 0 | 2,732 | 43.45% | 1.30 : 1 |
| **Devign (Dataset A)** | Test | 1,477 | 1,255 | 0 | 2,732 | 45.94% | 1.18 : 1 |
| **Devign Total** | Combined | 14,858 | 12,460 | 0 | 27,318 | 45.61% | 1.19 : 1 |
| **LLMVul (Dataset B)** | Train (Clean) | 13,455 | 1,176 | 0 | 14,631 | 8.04% | 11.44 : 1 |
| **LLMVul (Dataset B)** | Test (Clean) | 3,756 | 364 | 0 | 4,120 | 8.83% | 10.32 : 1 |
| **LLMVul (Dataset B)** | Quarantined | 0 | 0 | 2,679 | 2,679 | N/A | Excluded from primary binary eval |
| **LLMVul Total** | Full Release | 17,211 | 1,540 | 2,679 | 21,430 | 8.21%* | 11.18 : 1 |
| **SeCodePLT (Dataset C)** | Eval Pairs | 1,240 | 1,240 | 0 | 2,480 | 50.00% | 1.00 : 1 |
| **LLMVul Manual Gold** | Consensus | 2 | 83 | 15 | 100 | 97.65% | 0.02 : 1 |

*\*Vulnerability rate computed among high-confidence certain samples (18,751 total).*

---

## 2. Key Scientific Observations

1. **Devign Balance vs Real-World Class Imbalance:**
   - Devign is moderately balanced (~44.4% vulnerable, ~55.6% safe).
   - In contrast, LLMVul exhibits genuine production software class imbalance: ~8.2% vulnerable, ~91.8% safe.
   - This dramatic shift in positive prevalence is a primary driver of the precision degradation observed during cross-dataset evaluation.

2. **Quarantine of Uncertain Labels:**
   - In LLMVul, exactly 2,679 samples exhibited static tool divergence or ambiguous vulnerability signals.
   - Per Phase 2 requirements, these samples are preserved in `datasets/processed/llmvul_uncertain.jsonl` but strictly isolated from binary model evaluation to avoid injecting label noise into benchmark metrics.

3. **Stratified Repository Split in LLMVul:**
   - Both the Train (8.04% vuln) and Test (8.83% vuln) partitions maintain a consistent class distribution while strictly sharing zero repositories.
