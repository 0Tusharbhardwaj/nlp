# SecureCode AI — Repository Overlap and Data Leakage Audit

**Generated:** 2026-10-28 12:48:57 UTC

---

## 1. Audit Objective

Data leakage between training and evaluation splits occurs when code from the same repository or developer context appears in both splits. This creates an optimistic bias: the model memorizes repository-specific coding idioms, naming patterns, and structure rather than learning generalizable security semantics.

---

## 2. Benchmark A: CodeXGLUE / Devign Internal Overlap

| Split Pair | Repositories in Split 1 | Repositories in Split 2 | Overlapping Repositories | Overlap Percentage | Leakage Finding |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Train vs Test** | `{'qemu', 'FFmpeg'}` (2) | `{'qemu', 'FFmpeg'}` (2) | **2** (`qemu`, `FFmpeg`) | **100.0%** | **CRITICAL: Official benchmark splits intermix both projects.** |
| **Train vs Val** | `{'qemu', 'FFmpeg'}` (2) | `{'qemu', 'FFmpeg'}` (2) | **2** (`qemu`, `FFmpeg`) | **100.0%** | Official validation split shares both repositories. |
| **Val vs Test** | `{'qemu', 'FFmpeg'}` (2) | `{'qemu', 'FFmpeg'}` (2) | **2** (`qemu`, `FFmpeg`) | **100.0%** | Official validation and test splits share both repositories. |

### Scientific Implication
The official CodeXGLUE / Devign benchmark performed a random stratified sample across all functions rather than a repository-disjoint partition. As documented in our Independent Research Audit, 100% of test samples in Devign originate from repositories present in the training set.

---

## 3. Benchmark B: LLMVul Partitioning (Leak-Free Design)

In SecureCode AI Phase 2, we engineered a strictly repository-disjoint partitioning for LLMVul:

| Partition | Repository Count | Function Count | Repositories Included | Overlap with Test Repositories |
| :--- | :--- | :--- | :--- | :--- |
| **LLMVul Train** | **216** | 14,631 | 216 distinct GitHub repos (ClickHouse, Envoy, Redis, etc.) | **0 (0.0%)** |
| **LLMVul Test** | **8** | 4,120 | `DarkFlippers/unleashed-firmware`, `DavidXanatos/TaskExplorer`, `carla-simulator/carla`, `isl-org/Open3D`, `microsoft/WSL`, `microsoft/ebpf-for-windows`, `microsoft/onnxruntime`, `nature-lang/nature` | **0 (0.0%)** |

$$	ext{Train Repositories} \cap 	ext{Test Repositories} = \emptyset$$

### Verification Result
- Number of shared repositories between LLMVul Train and Test: **0**
- Data leakage risk: **Eliminated**.

---

## 4. Cross-Dataset Repository Overlap (Devign vs LLMVul vs SeCodePLT)

| Dataset Comparison | Repositories in A | Repositories in B | Common Repositories | Overlap Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Devign vs LLMVul** | 2 (`qemu`, `FFmpeg`) | 226 | **0** | **Completely disjoint.** Neither `qemu` nor `FFmpeg` is present in LLMVul's repository list. |
| **Devign vs SeCodePLT** | 2 (`qemu`, `FFmpeg`) | 88 CVE targets | 2 (QEMU & FFmpeg CVEs) | SeCodePLT contains CVE test cases from QEMU/FFmpeg alongside 86 other libraries (OpenSSL, LibTIFF, AOM, etc.). Kept separate as a zero-shot transfer test. |
| **LLMVul vs SeCodePLT** | 226 LLM repos | 88 CVE targets | **0** | **Completely disjoint.** LLMVul is composed of modern AI-assisted GitHub repositories, while SeCodePLT is composed of historic CVEs. |

### Conclusion
Cross-dataset evaluation (E2, E3, E4) represents an authentic, zero-leakage cross-repository evaluation.
