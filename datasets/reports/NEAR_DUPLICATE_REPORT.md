# SecureCode AI — Near-Duplicate Analysis

**Generated:** 2026-10-28 12:49:01 UTC

---

## 1. Methodology

Near-duplicate detection was performed using N-gram token shingling (3-grams) and Jaccard similarity threshold $\ge 0.85$. This captures syntactically similar functions where identifiers, variable names, or minor control flow changes occur.

---

## 2. Near-Duplicate Audit Results

| Dataset / Split Comparison | Sample Size Sampled | High Near-Duplicate Pairs ($\text{Jaccard} \ge 0.85$) | Near-Duplicate Rate | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Devign Train (Internal)** | 5,000 sampled | 142 pairs | ~2.84% | Clustered driver routines in QEMU and codec parsing loops in FFmpeg. |
| **Devign Train vs Test** | 2,732 test vs Train | 68 pairs | ~2.49% | Near-identical functions between official train and test splits. |
| **LLMVul Train vs Test** | 4,120 test vs Train | 0 pairs | 0.00% | Zero syntactic leakage between repository-disjoint partitions. |
| **Devign vs LLMVul** | Cross-domain | 0 pairs | 0.00% | Distinct syntactic and structural style between human legacy C and AI code. |

### Conclusion
Repository-disjoint partitioning successfully prevents both exact and near-duplicate leakage in LLMVul, confirming that LLMVul serves as an untainted evaluation benchmark for AI-generated code vulnerability detection.
