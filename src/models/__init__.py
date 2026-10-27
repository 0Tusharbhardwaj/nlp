"""Model architectures: TF-IDF classical baselines and CodeBERT sequence classifiers."""

from .baseline_tfidf import (
    BaseTFIDFClassifier,
    TFIDFLinearSVM,
    TFIDFLogisticRegression,
)

__all__ = [
    "BaseTFIDFClassifier",
    "TFIDFLogisticRegression",
    "TFIDFLinearSVM",
]
