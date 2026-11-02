# SecureCode AI — Viva Defense Guide & Examination Cheat Sheet

**Project:** SecureCode AI: Investigating the Domain Generalization Gap in Neural Vulnerability Detection  
**Level:** Undergraduate / Graduate Evaluation & Capstone Viva  
**Target:** Final Defense, Professor Oral Examination, and Project Demo  

---

## 1. The 60-Second Elevator Pitch (Memorize This)

> *"Our project investigates whether machine learning models trained on historical human-written code can reliably detect vulnerabilities in AI-generated code from Large Language Models.*  
>  
> *Rather than claiming 'whole-system security,' we strictly evaluate **static, function-level binary vulnerability detection** across three major benchmarks comprising over 51,000 C functions: CodeXGLUE/Devign, LLMVul, and SeCodePLT.*  
>  
> *Our central discovery is the **Domain Generalization Collapse**: while Microsoft CodeBERT achieves **66.36% accuracy and 64.71% Macro F1** on human code, its Macro F1 plummets by **-56.48% (down to 8.23%)** when evaluated zero-shot on LLM-generated code across isolated repositories. This happens because stylistic distribution shifts in AI code trigger massive false-positive surges. Furthermore, on paired CVE benchmark tasks (SeCodePLT), function-level sequence pooling yields **50.00% accuracy** (equivalent to a coin toss) because surgical 1-line patches are dominated by the unchanged surrounding context."*

---

## 2. Top 10 Viva Questions & Winning Answers

### Q1: Why did your professor ask you to remove the word "Security"?
* **Winning Answer:**  
  *"Software security is a comprehensive discipline spanning dynamic runtime exploit mitigations (ASLR, stack canaries), network perimeter firewalls, authentication, access control, and cryptographic key management. Machine learning classifiers operating on isolated source code text cannot guarantee system security. Therefore, we scientifically reframed our scope strictly as **static, function-level binary vulnerability classification**—identifying specific Common Weakness Enumerations (such as CWE-120 buffer overflows, CWE-78 command injection, and CWE-415 memory defects) in C source code."*

---

### Q2: Why did CodeBERT’s accuracy drop from 66.36% to 8.93% on LLMVul? Is your model broken?
* **Winning Answer:**  
  *"No, the model is not broken—this is the **primary scientific contribution of our paper**. It demonstrates that neural vulnerability classifiers suffer from severe domain shift.  
  CodeBERT was trained on human open-source code (QEMU/FFmpeg), learning human coding idioms. LLM-generated code has very distinct stylistic properties: synthetic identifier names, uniform indentation, and boilerplate structures.  
  The classifier interpreted these synthetic patterns as anomalous and flagged **99.9% of AI functions as vulnerable** (3,752 false positives out of 3,756 safe functions). While Recall was technically 100%, Macro F1 collapsed to 8.23%. This proves that deploying human-trained vulnerability detectors onto AI code pipelines without domain adaptation is dangerous."*

---

### Q3: What architecture and hyperparameters did you use to train CodeBERT?
* **Winning Answer:**  
  - **Backbone:** `microsoft/codebert-base` (bimodal RoBERTa architecture: 12 transformer layers, 768 hidden dimensions, 12 attention heads, 125 million parameters).
  - **Classification Head:** Dense(768, 768) + Tanh activation + Dropout(0.1) + Dense(768, 2) sequence pooling on the leading `<s>` classification token.
  - **Dataset:** 21,854 C functions from the official Devign training split.
  - **Optimizer:** AdamW with weight decay $\lambda = 0.01$.
  - **Learning Rate:** Peak $\alpha = 2 \times 10^{-5}$ with a **Cosine Learning Rate Decay** schedule.
  - **Warmup:** Dynamic linear warmup over the first 10% of training (**341 warmup steps**).
  - **Batch Size:** 16 samples per batch, trained for 3 complete epochs (4,098 total optimization steps).
  - **Precision:** FP16 Automatic Mixed Precision (`torch.cuda.amp`) executed on an NVIDIA GPU.

---

### Q4: How do your classical baselines compare against CodeBERT?
* **Winning Answer:**  
  *"We implemented two classical lexical baselines using sublinear word and operator token TF-IDF n-grams $(1, 2)$:  
  1. **Balanced Logistic Regression:** Achieved 61.35% accuracy and 61.30% Macro F1 with an inference latency of **4.8 ms**.  
  2. **Linear SVM with Platt Scaling:** Achieved 59.44% accuracy and 58.48% Macro F1.  
  CodeBERT outperformed both on human code (**66.36% accuracy, 64.71% Macro F1, and 0.7301 ROC-AUC**), demonstrating that multi-head contextual self-attention captures semantic dependencies that bag-of-words models miss. However, classical models run in <15ms on CPU, making them useful as lightweight initial filters."*

---

### Q5: What is Platt Scaling and why was it necessary for your Linear SVM?
* **Winning Answer:**  
  *"A standard Linear Support Vector Machine outputs an uncalibrated geometric margin distance to the decision hyperplane: $f(x) = \mathbf{w}^T x + b$. This is not a probability.  
  In a security dashboard, developers require meaningful confidence percentages. We applied **Platt scaling** via cross-validated sigmoid calibration (`CalibratedClassifierCV`):  
  $$P(y=1 \mid x) = \frac{1}{1 + \exp(A \cdot f(x) + B)}$$  
  This maps arbitrary margin distances into calibrated, well-behaved posterior probabilities $[0.0, 1.0]$."*

---

### Q6: What did you uncover regarding data leakage in the Devign benchmark?
* **Winning Answer:**  
  *"During our data hygiene audit, we discovered that the official CodeXGLUE / Devign test split shares **100% of its source repositories** (`qemu` and `ffmpeg`) with the training split.  
  Furthermore, exact string hashing revealed **10 character-identical functions** shared across train and test sets, and **57 functions** with contradictory labels (exact identical code labeled as both safe and vulnerable).  
  This demonstrates that high benchmarks reported in academic literature often reflect repository memorization and author coding style rather than pure vulnerability comprehension."*

---

### Q7: How did you ensure 0% data leakage when evaluating on LLMVul?
* **Winning Answer:**  
  *"Instead of randomly shuffling functions (which leaks repository conventions), we engineered a greedy, deterministic **repository-disjoint partitioner** (`src/data/llmvul_partitioner.py`).  
  We isolated **8 complete repositories (4,120 functions)** strictly into the holdout cohort, ensuring:  
  $$\text{Train Repositories} \cap \text{Holdout Repositories} = \emptyset$$  
  Furthermore, we quarantined 2,679 ambiguous `NaN` labels where automated verification tools disagreed."*

---

### Q8: Why did CodeBERT get exactly 50.00% accuracy on the SeCodePLT CVE benchmark?
* **Winning Answer:**  
  *"SeCodePLT (NeurIPS 2024) consists of 2,480 balanced pairs: 1,240 verified vulnerable functions and their corresponding 1,240 security patches.  
  In 99.8% of cases, CodeBERT predicted BOTH the vulnerable function AND the patched function as vulnerable (ROC-AUC was **0.4993**, effectively a random coin toss).  
  In real-world C software, a security patch often modifies only 1–3 lines (e.g., adding `if (len >= MAX) return -1;`). Because sequence-level classification heads pool representations across all 512 input tokens, the 95%+ unchanged token context completely drowns out the localized patch."*

---

### Q9: How do you handle code comments without breaking code semantics?
* **Winning Answer:**  
  *"Naive regular expressions like `re.sub(r'//.*', '', code)` break code by corrupting string literals containing slash characters (such as URLs like `\"https://api...\"`).  
  To solve this, we built a deterministic **5-state lexer state machine** (`src/preprocessing/safe_cleaner.py`):  
  $$S \in \{\text{NORMAL}, \text{IN\_STRING}, \text{IN\_CHAR}, \text{IN\_LINE\_COMMENT}, \text{IN\_BLOCK\_COMMENT}\}$$  
  This safely strips developer comments while preserving string literals, escape sequences, pointer dereferences, and macro boundaries."*

---

### Q10: What is your concrete engineering recommendation?
* **Winning Answer:**  
  *"Organizations deploying AI code generators (like Copilot or Cursor) **must not** rely on vulnerability classifiers trained exclusively on human open-source code. Effective security review for AI code requires:  
  1. Domain-adapted fine-tuning on AI-synthesized corpora.  
  2. Contrastive patch-level loss formulations rather than sequence-level pooling.  
  3. Hybrid defense pairing neural models with dynamic address sanitizers (ASan) and formal fuzzing."*

---

## 3. Live Demonstration Cheat Sheet (How to Demo to Examiners)

### Step 1: Launch Application
- Double-click [`run_app.bat`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/run_app.bat).
- Open `http://localhost:5173` in your browser.

### Step 2: Show Preset Vulnerability Scanning
1. Click **Preset: Buffer Overflow (CWE-120)**:
   - Point out unbounded `strcpy(internal_buffer, user_input)`.
   - Click **"Scan Code for Vulnerabilities"**.
   - Show the result: **VULNERABLE (Class 1) - 97.5% Confidence**.
   - Point out the latency (**~4 ms for SVM, sub-50ms for CodeBERT on your RTX 3050**).
2. Click **Preset: Safe Bounds-Checked**:
   - Point out `strncpy(internal_buffer, user_input, sizeof(internal_buffer) - 1);`.
   - Click **"Scan Code"**.
   - Show result: **SAFE (Class 0) - 94.2% Confidence**.
3. Click **Preset: AI-Generated Socket Handler**:
   - Point out how AI boilerplates trigger the cross-domain vulnerability flag.

### Step 3: Show the Benchmark Analytics Tab
- Click the **"Cross-Dataset (E1-E4)"** tab.
- Walk the professor through the side-by-side confusion matrix:
  - **Devign In-Distribution**: High precision (68.96%), balanced classification.
  - **LLMVul AI Holdout**: The massive false-positive column (3,752 false positives) proving the domain shift collapse.

### Step 4: Show the Research Artifacts & GPU Setup
- Point to [`docs/RESEARCH_PAPER.md`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/RESEARCH_PAPER.md).
- Point to the submission package [`docs/paper/overleaf_package.zip`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/docs/paper/overleaf_package.zip).
- Point to [`launch_jupyter_gpu.bat`](file:///c:/Users/tusha/OneDrive/Desktop/sem%205/nlp/launch_jupyter_gpu.bat) and mention:
  *"Everything was reproduced, audited, and executed locally on our NVIDIA RTX 3050 GPU under an Anaconda environment with 44 passing unit tests."*

