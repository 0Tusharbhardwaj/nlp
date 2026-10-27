"""Evaluation metrics, cross-dataset evaluation harness, and confusion matrix generators."""

from .cross_evaluator import (
    CrossDatasetEvaluator,
    partition_disjoint_by_repository,
)
from .metrics import compute_vulnerability_metrics
from .visualizer import plot_baseline_comparison, plot_confusion_matrix

__all__ = [
    "compute_vulnerability_metrics",
    "plot_confusion_matrix",
    "plot_baseline_comparison",
    "CrossDatasetEvaluator",
    "partition_disjoint_by_repository",
]
