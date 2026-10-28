# SecureCode AI — Full Dataset Statistics

**Generated:** 2026-10-28 12:48:57 UTC

---

## 1. Dataset A: CodeXGLUE / Devign

### Partition Record Counts
- **Train:** 21,854 functions (79.998%)
- **Validation:** 2,732 functions (10.001%)
- **Test:** 2,732 functions (10.001%)
- **Combined Total:** 27,318 functions

### Column Schemas & Missing Values
| Column Name | Data Type | Nulls (Train) | Nulls (Val) | Nulls (Test) | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | int32 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | Unique benchmark sample index |
| `func` | string | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | Full C function source code |
| `target` | bool | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | Ground-truth defect label (1: vulnerable, 0: safe) |
| `project` | string | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | Origin repository ('qemu' or 'FFmpeg') |
| `commit_id` | string | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | Git commit identifier |

### Project Distribution in Devign
| Split | QEMU Functions | FFmpeg Functions | Total | QEMU % |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 14,032 | 7,822 | 21,854 | 64.21% |
| **Validation** | 1,761 | 971 | 2,732 | 64.46% |
| **Test** | 1,756 | 976 | 2,732 | 64.28% |
| **Total** | 17,549 | 9,769 | 27,318 | 64.24% |

---

## 2. Dataset B: LLMVul (Production LLM Benchmark)

### Record Counts & Label Stratification
- **Total Mined Records:** 21,430
- **High-Confidence Certain Records:** 18,751 (87.50%)
- **Quarantined Uncertain Records:** 2,679 (12.50%)
- **Number of Unique Repositories:** 226

### AI Tool Provenance (Generation Origin)
| AI Tool / Assistant | Certain Count | Uncertain Count | Total Count | Relative Share |
| :--- | :--- | :--- | :--- | :--- |
| `claude_code` | 12,243 | 1,978 | 14,221 | 66.36% |
| `copilot` | 4,502 | 450 | 4,952 | 23.11% |
| `claude` | 741 | 66 | 807 | 3.77% |
| `gemini` | 338 | 48 | 386 | 1.80% |
| `cursor` | 337 | 36 | 373 | 1.74% |
| `chatgpt` | 238 | 60 | 298 | 1.39% |
| `generic_llm` | 215 | 27 | 242 | 1.13% |
| `openai_codex` | 123 | 12 | 135 | 0.63% |
| `devin` | 14 | 2 | 16 | 0.07% |
| **Total** | **18,751** | **2,679** | **21,430** | **100.0%** |

### Language Distribution
- **C++ (`cpp`):** 12,546 (58.54%)
- **C (`c`):** 8,884 (41.46%)

### Static Analysis Agreement Signals
- **Strong Signal (Multi-tool or confirmed):** 19,121 (89.23%)
- **Medium Signal:** 2,309 (10.77%)

---

## 3. Dataset C: SeCodePLT

- **Benchmark Subtask:** `c_vulnerability_detection`
- **Total Tasks:** 1,240 CVE-grounded instances
- **Generated Evaluation Pairs:** 2,480 functions (1,240 vulnerable + 1,240 safe)
- **Primary Weakness Categories:** Buffer Overflow (CWE-119, CWE-120), Out-of-bounds Read/Write (CWE-125, CWE-787), Use After Free (CWE-416), Integer Overflow (CWE-190).
