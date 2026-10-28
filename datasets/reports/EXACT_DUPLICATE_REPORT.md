# SecureCode AI — Exact Duplicate and Label Collision Audit

**Generated:** 2026-10-28 12:48:58 UTC

---

## 1. Executive Findings

Exact code duplicates occur when two functions are character-for-character identical after normalizing whitespace. Label collisions occur when the identical code string is labeled vulnerable ($1$) in one record and safe ($0$) in another.

---

## 2. Devign Exact Duplicate Audit

| Audit Dimension | Metric | Percentage of Split | Research Impact |
| :--- | :--- | :--- | :--- |
| **Devign Train Internal Duplicates** | **58** | 0.27% | Repetitive utility macros and boilerplate functions in QEMU/FFmpeg |
| **Devign Train vs Test Duplicate Code** | **10** | 0.37% | **Train-to-test memorization hazard** in official CodeXGLUE test set |
| **Devign Train vs Val Duplicate Code** | **8** | 0.29% | Validation checkpoint selection hazard |
| **Devign Train Label Contradictions** | **57** | 0.26% | Identical function text assigned conflicting labels (0 and 1) |

### Key Discovery
In the official Devign test split, **10 functions** (0.37% of the test set) are exact duplicates of functions in the training split. This further reinforces the necessity of external, repository-disjoint evaluation on LLMVul.

---

## 3. LLMVul Exact Duplicate Audit

| Audit Dimension | Metric | Percentage of Split | Assessment |
| :--- | :--- | :--- | :--- |
| **LLMVul Train Internal Duplicates** | **527** | 3.60% | Common LLM-generated scaffolding and repetitive accessor stubs |
| **LLMVul Train vs Test Duplicate Code** | **0** | 0.00% | Negligible overlap across disjoint repositories |
| **LLMVul Label Contradictions** | **0** | 0.0% | Multi-tool ensemble voting prevents label contradictions |

---

## 4. Cross-Dataset Code Overlap (Devign vs LLMVul)

| Metric | Value | Implication |
| :--- | :--- | :--- |
| **Exact Function Overlap (Devign $\cap$ LLMVul)** | **0** | **0.0% code leakage.** |

The zero code overlap between Devign and LLMVul guarantees that models evaluated on LLMVul cannot rely on verbatim function memorization.
