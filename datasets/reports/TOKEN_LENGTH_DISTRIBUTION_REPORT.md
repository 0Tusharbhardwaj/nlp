# SecureCode AI — Token-Length Distribution and Truncation Analysis

**Generated:** 2026-10-28 12:49:01 UTC

---

## 1. Executive Summary

Transformer models such as CodeBERT (`microsoft/codebert-base`) enforce a rigid maximum sequence length ($L_\text{max} = 512$). Functions exceeding $L_\text{max}$ are truncated, causing vulnerability indicators located near the end of functions to be silently dropped. This analysis measures token length percentiles and truncation risk across all benchmark cohorts.

---

## 2. Token-Length Distribution Percentiles

| Benchmark Split | Sample Count | Min | P25 | Median (P50) | P75 | P90 | P95 | P99 | Max | Mean $\pm$ Std |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Devign Train** | 21,854 | 7 | 88 | **206** | 477 | 970 | 1511 | 3321 | 26,336 | 438.6 $\pm$ 896.3 |
| **Devign Test** | 2,732 | 7 | 92 | **214** | 497 | 950 | 1446 | 3032 | 26,336 | 432.0 $\pm$ 885.9 |
| **LLMVul Train** | 14,631 | 9 | 60 | **111** | 210 | 379 | 534 | 926 | 3,019 | 172.7 $\pm$ 186.7 |
| **LLMVul Test** | 4,120 | 10 | 53 | **102** | 225 | 435 | 584 | 967 | 1,473 | 178.3 $\pm$ 197.6 |
| **SeCodePLT Eval**| 2,480 | 0 | 244 | **566** | 1209 | 3452 | 5744 | 12396 | 33,900 | 1400.9 $\pm$ 2623.0 |

---

## 3. Truncation Impact Analysis

| Benchmark Split | Exceeds 128 Tokens (%) | Exceeds 256 Tokens (%) | Exceeds 512 Tokens (CodeBERT Limit) (%) | Complete Coverage at $L=512$ (%) |
| :--- | :--- | :--- | :--- | :--- |
| **Devign Train** | 64.52% | 42.97% | **23.12%** | **76.88%** |
| **Devign Test** | 65.63% | 43.96% | **24.27%** | **75.73%** |
| **LLMVul Train** | 43.48% | 19.00% | **5.47%** | **94.53%** |
| **LLMVul Test** | 42.09% | 21.33% | **7.06%** | **92.94%** |
| **SeCodePLT Eval**| 87.42% | 73.06% | **53.10%** | **46.90%** |

### Critical Engineering Findings
1. **CodeBERT Maximum Length ($L=512$):**
   - At $L=512$, **76.9%** of Devign functions and **94.5%** of LLMVul functions are fully captured without truncation.
   - For the ~23.1% of functions exceeding 512 tokens, truncation preserves the function signature, local declarations, and initial branch structures.
2. **LLM vs Human Code Verbosity:**
   - LLMVul functions have a median token length of **111 tokens**, compared to **206 tokens** for human-written Devign functions.
   - LLM-generated functions in production repositories are significantly more modular and concise than legacy C codebases like QEMU and FFmpeg.
