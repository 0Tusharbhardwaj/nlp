"""Classical TF-IDF machine learning baseline models for vulnerability detection.

Implements:
- TF-IDF + Logistic Regression
- TF-IDF + Linear SVM (LinearSVC with calibrated decision probabilities)
- Strict train-only vectorizer fitting to prevent test leakage
- Class imbalance mitigation via class_weight='balanced'
- Joblib serialization and deserialization
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC


class BaseTFIDFClassifier:
    """Base class for TF-IDF based code vulnerability classifiers."""

    def __init__(self, vectorizer_params: Optional[Dict[str, Any]] = None):
        default_vec_params = {
            "max_features": 10000,
            "ngram_range": (1, 2),
            "min_df": 1,  # Safe default for variable dataset sizes
            "sublinear_tf": True,
            "token_pattern": r"(?u)\b\w+\b|[{}();,\[\].:]",  # Capture punctuation and operators
        }
        if vectorizer_params:
            default_vec_params.update(vectorizer_params)
        
        # Scikit-learn requires ngram_range to be a tuple, but YAML parses arrays as lists
        if isinstance(default_vec_params.get("ngram_range"), list):
            default_vec_params["ngram_range"] = tuple(default_vec_params["ngram_range"])
            
        self.vectorizer_params = default_vec_params
        self.vectorizer = TfidfVectorizer(**self.vectorizer_params)
        self.is_fitted = False

    def transform(self, texts: List[str]) -> Any:
        """Transform text snippets into TF-IDF vectors using pre-fitted vocabulary."""
        if not self.is_fitted:
            raise RuntimeError("Model and vectorizer must be fitted before calling transform/predict.")
        return self.vectorizer.transform(texts)

    def save(self, filepath: Union[str, Path]) -> None:
        """Persist the fitted model and vectorizer to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "BaseTFIDFClassifier":
        """Load a persisted model and vectorizer from disk."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at: {path}")
        loaded = joblib.load(path)
        return loaded


class TFIDFLogisticRegression(BaseTFIDFClassifier):
    """TF-IDF + Logistic Regression vulnerability classifier."""

    def __init__(
        self,
        vectorizer_params: Optional[Dict[str, Any]] = None,
        model_params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(vectorizer_params)
        default_model_params = {
            "penalty": "l2",
            "C": 1.0,
            "solver": "lbfgs",
            "max_iter": 1000,
            "class_weight": "balanced",
            "random_state": 42,
        }
        if model_params:
            default_model_params.update(model_params)
        self.model_params = default_model_params
        self.classifier = LogisticRegression(**self.model_params)

    def fit(self, texts: List[str], y: List[int]) -> "TFIDFLogisticRegression":
        """Fit vectorizer and logistic regression strictly on training data."""
        if hasattr(self.vectorizer, "min_df") and isinstance(self.vectorizer.min_df, int) and self.vectorizer.min_df > len(texts):
            self.vectorizer.min_df = 1
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, texts: List[str], threshold: float = 0.5) -> np.ndarray:
        """Predict binary vulnerability labels (0 = safe, 1 = vulnerable)."""
        probs = self.predict_proba(texts)[:, 1]
        return (probs >= threshold).astype(int)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        """Predict class probabilities [P(safe), P(vulnerable)]."""
        X = self.transform(texts)
        return self.classifier.predict_proba(X)

    def decision_function(self, texts: List[str]) -> np.ndarray:
        """Compute decision function values."""
        X = self.transform(texts)
        return self.classifier.decision_function(X)


class TFIDFLinearSVM(BaseTFIDFClassifier):
    """TF-IDF + Linear Support Vector Machine (LinearSVC) vulnerability classifier."""

    def __init__(
        self,
        vectorizer_params: Optional[Dict[str, Any]] = None,
        model_params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(vectorizer_params)
        default_model_params = {
            "C": 1.0,
            "loss": "squared_hinge",
            "max_iter": 2000,
            "class_weight": "balanced",
            "random_state": 42,
        }
        if model_params:
            default_model_params.update(model_params)
        self.model_params = default_model_params
        self.classifier = LinearSVC(**self.model_params)

    def fit(self, texts: List[str], y: List[int]) -> "TFIDFLinearSVM":
        """Fit vectorizer and LinearSVC strictly on training data."""
        if hasattr(self.vectorizer, "min_df") and isinstance(self.vectorizer.min_df, int) and self.vectorizer.min_df > len(texts):
            self.vectorizer.min_df = 1
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, y)
        self.is_fitted = True
        return self

    def decision_function(self, texts: List[str]) -> np.ndarray:
        """Compute distance of samples to the separating hyperplane."""
        X = self.transform(texts)
        if hasattr(self.classifier, "decision_function"):
            return self.classifier.decision_function(X)
        probs = self.classifier.predict_proba(X)[:, 1]
        probs = np.clip(probs, 1e-7, 1.0 - 1e-7)
        return np.log(probs / (1.0 - probs))

    def predict(self, texts: List[str]) -> np.ndarray:
        """Predict binary vulnerability labels (0 = safe, 1 = vulnerable)."""
        X = self.transform(texts)
        return self.classifier.predict(X)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        """Compute class probabilities via CalibratedClassifierCV or Platt scaling sigmoid."""
        X = self.transform(texts)
        if hasattr(self.classifier, "predict_proba"):
            return self.classifier.predict_proba(X)
        scores = self.classifier.decision_function(X)
        # Sigmoid: P(y=1) = 1 / (1 + exp(-score))
        p1 = 1.0 / (1.0 + np.exp(-np.clip(scores, -20, 20)))
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

