# SecureCode AI — Final Research Paper & System Development Roadmap

**Project Title:** SecureCode AI: An Intelligent Framework for Source Code Vulnerability Detection, Domain Adaptation, and AI-Code Analysis  
**Scope Boundary:** Static, function-level and patch-level binary vulnerability classification in C/C++ source code.  
**Explicit Non-Claims:** Does not claim whole-system security, runtime exploit mitigation, penetration testing, or general application defense. The term "security" denotes the broader research field, not a platform assurance claim.  
**Compute Infrastructure:** Local NVIDIA GeForce RTX 3050 Laptop GPU (6 GB VRAM, CUDA 12.4, FP16 mixed precision via `nlp_gpu` environment).  

---

## 1. Scientific Principles & Key Methodological Corrections

Following critical peer review, this roadmap enforces five methodological rules across all empirical reporting:

1. **Exact Generalization Gap Reporting:**  
   The performance gap between human in-distribution (E1: 64.71% Macro F1) and zero-shot AI transfer (E2: 8.23% Macro F1) is reported as a **56.48-percentage-point drop** ($\Delta = -56.48\text{ pp}$), avoiding ambiguous relative percentage phrasing.
2. **Defensible False Positive Reporting:**  
   Rather than ungrounded claims, report exact confusion matrix counts and derived rates:
   - On the LLMVul holdout ($N=4,120$), the human-trained model produced:
     - $\text{True Negatives (TN)} = 4$
     - $\text{False Positives (FP)} = 3,752$
     - $\text{False Negatives (FN)} = 0$
     - $\text{True Positives (TP)} = 364$
   - This yields $\text{Recall} = 100.0\%$, $\text{Precision} = 8.84\%$, and a False Positive Rate of:
     $$\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}} = \frac{3,752}{3,752 + 4} = 99.89\%$$
   The model pathologically flags almost every AI sample as anomalous.
3. **Careful Framing of Code Origin Estimation:**  
   The component formerly described as an "AI detector" is formally designated as the **Code Origin Estimator** (or **AI-Code Provenance Estimator**). It estimates whether an input snippet syntactically and lexically resembles the human-written or AI-generated distributions in its training corpora. It outputs three calibrated states:
   $$\text{Decision} \in \{\text{Human-like}, \text{AI-like}, \text{Uncertain / Abstain}\}$$
   The Origin Estimator and Vulnerability Detectors are evaluated **independently** before measuring end-to-end composite pipeline routing.
4. **Transparent Data Leakage Distinction:**  
   - We programmatically document that the standard **Devign benchmark suffers from repository leakage** (100% of repositories shared between train and test splits, 10 exact duplicate functions, 57 contradictory labels).
   - In contrast, our **LLMVul evaluation partition enforces a strictly repository-disjoint partition** (0% shared repositories between train and holdout splits).
5. **Aspirational vs. Realized Metrics:**  
   Target numbers (e.g., >70% Macro F1 recovery, >75% patch discrimination) are treated strictly as experimental hypotheses, never presented as results until empirical execution on the RTX 3050 is complete.

---

## 2. The 5-Phase Development Roadmap

```mermaid
flowchart TD
    subgraph Phase 1: Domain Adaptation (Highest Priority)
        E1["E1: Human Baseline (64.71% F1) [Done]"]
        E2["E2: Zero-Shot AI Evaluation (8.23% F1) [Done]"]
        E3["E3: Joint Training (Devign 21,854 + LLMVul 14,631)"]
        E4["E4: AI-Native Training (LLMVul 14,631 Only)"]
        E1 & E2 & E3 & E4 --> EVAL1["Comparative Matrix: Precision, Recall, Macro F1, FPR, FNR"]
    end

    subgraph Phase 2: Patch-Level Vulnerability Detection
        SE1["SeCodePLT Paired CVE Dataset (1,240 Tasks = 2,480 Samples)"]
        SE1 --> SE2["Strict CVE-Disjoint Split (Train vs. Test CVEs)"]
        SE2 --> SE3["Differential Siamese Encoder: d = |h_vuln - h_patch|"]
        SE3 --> SE4["Compare Standard Sequence CodeBERT vs. Differential Head"]
    end

    subgraph Phase 3: Code Origin Estimation & Adaptive Routing
        OR1["Train Lightweight Code Origin Estimator (TF-IDF + Ridge/Linear)"]
        OR1 --> OR2["Three-Way Output: Human-like, AI-like, Uncertain"]
        OR2 --> OR3["Independent Evaluation of Origin Estimator"]
        OR3 --> OR4["Adaptive Dispatch to Specialized Detectors"]
        OR4 --> OR5["FastAPI Endpoint + React UI Integration"]
    end

    subgraph Phase 4: Cross-Architecture Evaluation (Resource Permitting)
        AR1["CodeBERT (Sequence Transformer)"]
        AR2["GraphCodeBERT (Dataflow Graph Transformer)"]
        AR3["UniXcoder (Multimodal Transformer)"]
        AR1 & AR2 & AR3 --> AR4["Analyze Memory, Latency, and Resistance to AI Stylistic Shift"]
    end

    subgraph Phase 5: Final Research Paper & Platform Validation
        FIN1["Ablation Studies & Qualitative Case Studies"]
        FIN2["Threats to Validity & Explicit Limitations"]
        FIN3["Submission-Ready IEEE/ACM Research Paper Draft"]
        FIN4["Production Artifact & Full-Scale Demo"]
    end

    Phase 1 --> Phase 2
    Phase 2 --> Phase 3
    Phase 3 --> Phase 4
    Phase 4 --> Phase 5
```

---

## 3. Detailed Execution Specifications

### Phase 1: Domain Adaptation (E3 & E4 on Local RTX 3050)
* **Objective:** Establish the empirical recovery achieved by domain adaptation.
* **Hardware Configuration (6 GB VRAM Optimization):**
  - **Backbone:** `microsoft/codebert-base` (125M parameters).
  - **Precision:** FP16 Automatic Mixed Precision (`torch.cuda.amp`).
  - **Per-Device Batch Size:** 4 samples.
  - **Gradient Accumulation Steps:** 8 (effective batch size = 32).
  - **Max Sequence Length:** 512 tokens.
  - **Optimizer:** AdamW ($\text{lr} = 2 \times 10^{-5}$, weight decay $\lambda = 0.01$).
  - **Scheduler:** Cosine annealing with 10% dynamic linear warmup.
* **Datasets:**
  - **E4 (AI-Native):** Train on `datasets/processed/llmvul_train_clean.jsonl` ($N=14,631$) $\rightarrow$ Test on `datasets/processed/llmvul_test_clean.jsonl` ($N=4,120$).
  - **E3 (Joint Adaptation):** Train on Combined ($21,854 \text{ Devign} + 14,631 \text{ LLMVul} = 36,485\text{ samples}$) $\rightarrow$ Test on `llmvul_test_clean.jsonl`.
* **Output:** Exact comparison table measuring Macro F1, Recall, Precision, FPR, and FNR across E1, E2, E3, and E4.

---

### Phase 2: Patch-Level Vulnerability Detection (SeCodePLT)
* **Objective:** Overcome the 50.00% random-guessing limitation on surgical 1–3 line vulnerability patches.
* **Experimental Rigor:**
  - Enforce **CVE-disjoint splitting**: CVE identifiers present in the training pairs must never appear in the test set.
* **Architecture:**
  - Siamese twin forward pass with shared CodeBERT weights:
    $$\mathbf{h}_{\text{vuln}} = \text{Encoder}(x_{\text{vuln}}), \quad \mathbf{h}_{\text{patch}} = \text{Encoder}(x_{\text{patch}})$$
    $$\mathbf{d} = |\mathbf{h}_{\text{vuln}} - \mathbf{h}_{\text{patch}}|$$
    $$\hat{y} = \text{ClassifierHead}([\mathbf{h}_{\text{vuln}}, \mathbf{h}_{\text{patch}}, \mathbf{d}])$$
* **Baseline Comparison:** Directly compare the differential classifier against standard function-level sequence CodeBERT.

---

### Phase 3: Code Origin Estimation & Adaptive Routing
* **Origin Estimator Design:**
  - Fast lexical and syntactic feature extractor (n-grams, casing conventions, comment density, API idiom repetition).
  - Output probabilities $P(\text{Human})$ and $P(\text{AI})$.
  - If $|P(\text{Human}) - P(\text{AI})| < 0.20$, classify as **Uncertain / Abstain**.
* **Two-Stage Evaluation:**
  1. *Stage 1:* Evaluate origin estimator accuracy, precision, and abstain rate independently.
  2. *Stage 2:* Evaluate composite system routing: does routing AI-like code to the domain-adapted model and human-like code to the human-trained model outperform a single monolithic model?
* **Product Integration:** Expose `/api/v1/scan/adaptive` in FastAPI and integrate toggle into the React dashboard.

---

### Phase 4: Cross-Architecture Evaluation (Resource Permitting)
* Compare CodeBERT (sequence tokens) against GraphCodeBERT (sequence + data-flow edges).
* Test the research hypothesis: *Does incorporating semantic data-flow graphs improve resilience against LLM stylistic variation?*

---

### Phase 5: Final Publication Deliverables
* Complete 8-page IEEE conference paper in `docs/paper/main.tex`.
* Full transparency section detailing threats to validity, dataset limitations, and computational budgets.
* Comprehensive reproduction package and live demonstration setup.

---

## 4. Immediate Action Item

The immediate priority is **Phase 1: Domain Adaptation (E3 & E4)**:
1. Construct the joint training partition combining Devign train ($N=21,854$) and LLMVul clean train ($N=14,631$).
2. Implement the local training harness configured for our 6 GB RTX 3050 (batch size 4, gradient accumulation 8, FP16).
3. Execute the training runs, evaluate on the 4,120 disjoint holdout set, and record the real empirical metrics.
