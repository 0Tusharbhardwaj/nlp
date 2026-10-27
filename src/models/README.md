# SecureCode AI — Classical ML Baselines Documentation

## 1. Overview

This module provides reproducible, production-grade implementations of the two primary classical machine learning baselines for source-code vulnerability detection:
1. **TF-IDF + Logistic Regression**
2. **TF-IDF + Linear Support Vector Machine (Linear SVM)**

Both models operate on preprocessed source code extracted from the validated CodeXGLUE / Devign benchmark.

---

## 2. Mathematical Formulations & Architecture

### 2.1 Term Frequency - Inverse Document Frequency (TF-IDF)
For code vocabulary terms $t$ and function code sample $d$:
$$\text{TF}(t, d) = 1 + \log(\text{count}(t, d)) \quad \text{if } \text{count}(t, d) > 0 \text{ (Sublinear TF)}$$
$$\text{IDF}(t, D) = \log\left(\frac{1 + |D|}{1 + |\{d \in D : t \in d\}|}\right) + 1$$
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \text{IDF}(t, D)$$

Features:
- N-gram Range: (1, 2) [unigrams and bigrams]
- Max Features: 10,000
- Token Pattern: Captures alphanumeric tokens, punctuation, brackets, and operators (`[{}();,\[\].:]`) to preserve syntactic program boundaries.

### 2.2 Baseline 1: Logistic Regression
Minimizes the regularized negative log-likelihood with balanced class weights:
$$\min_{\mathbf{w}, b} \frac{1}{2} \|\mathbf{w}\|_2^2 + C \sum_{i=1}^N w_{y_i} \log\left(1 + \exp(-y_i (\mathbf{w}^T \mathbf{x}_i + b))\right)$$
- Solver: L-BFGS
- Class Weight: `balanced` (inversely proportional to class frequencies $w_c = \frac{N}{2 N_c}$)
- Decision Rule: $\hat{y} = 1$ if $P(y=1|\mathbf{x}) \ge 0.5$

### 2.3 Baseline 2: Linear SVM (LinearSVC)
Solves the soft-margin optimization problem with squared-hinge loss:
$$\min_{\mathbf{w}, b} \frac{1}{2} \|\mathbf{w}\|_2^2 + C \sum_{i=1}^N w_{y_i} \max\left(0, 1 - y_i (\mathbf{w}^T \mathbf{x}_i + b)\right)^2$$
- Loss: `squared_hinge`
- Class Weight: `balanced`
- Probability Approximation: Platt scaling sigmoid on decision function values $P(y=1) = \frac{1}{1 + \exp(-\text{score})}$.

---

## 3. Scientific Metric Definitions

In software vulnerability detection, failing to flag a vulnerability (False Negative) has catastrophic security consequences compared to a false alarm. Hence:

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$
$$\text{Precision} = \frac{TP}{TP + FP}$$
$$\text{Recall} = \frac{TP}{TP + FN}$$
$$\text{F1-Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
$$\mathbf{False\ Negative\ Rate\ (FNR)} = \frac{FN}{TP + FN} = 1 - \text{Recall}$$
$$\text{ROC-AUC} = \text{Area under ROC curve computed across continuous prediction scores}$$

---

## 4. Reproducing Baselines

Run training via the CLI runner:

```bash
python scripts/train_baselines.py --config configs/base.yaml --dataset devign
```

### Generated Artifacts:
- **Models**:
  - `results/models/tfidf_logistic_regression.joblib`
  - `results/models/tfidf_linear_svm.joblib`
- **Metrics**:
  - `results/metrics/baseline_metrics.json`
  - `results/metrics/baseline_metrics.csv`
  - `results/metrics/baseline_experiment_config.json`
- **Figures**:
  - `results/figures/logistic_regression_cm.png`
  - `results/figures/linear_svm_cm.png`
  - `results/figures/baselines_comparison.png`
- **Training Logs**:
  - `results/logs/baseline_training.log`

---

## 5. Loading Models for Inference

```python
from src.models import TFIDFLogisticRegression, TFIDFLinearSVM

# Load saved model and fitted vectorizer
model = TFIDFLogisticRegression.load("results/models/tfidf_logistic_regression.joblib")

code_snippet = """
static void copy_data(char *dst, const char *src) {
    strcpy(dst, src); // Unbounded copy
}
"""

prediction = model.predict([code_snippet])[0]
probabilities = model.predict_proba([code_snippet])[0]

print(f"Prediction: {'Vulnerable' if prediction == 1 else 'Safe'}")
print(f"Vulnerability Probability: {probabilities[1]:.4f}")
```
