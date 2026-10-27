"""Visualization utilities for confusion matrices, ROC curves, and model comparisons."""

from pathlib import Path
from typing import Any, Dict, List
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend suitable for scripts and servers
import matplotlib.pyplot as plt
import numpy as np


def plot_confusion_matrix(
    cm_dict: Dict[str, int],
    title: str = "Confusion Matrix",
    output_path: Path = None,
    cmap: str = "Blues",
) -> None:
    """Plot an annotated 2x2 confusion matrix heatmap and save as an image.
    
    Args:
        cm_dict: Dictionary with keys 'tn', 'fp', 'fn', 'tp'.
        title: Title of the figure.
        output_path: Target filepath to save PNG image.
        cmap: Matplotlib colormap name.
    """
    tn = cm_dict.get("tn", 0)
    fp = cm_dict.get("fp", 0)
    fn = cm_dict.get("fn", 0)
    tp = cm_dict.get("tp", 0)

    matrix = np.array([[tn, fp], [fn, tp]])
    total = np.sum(matrix)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
    im = ax.imshow(matrix, interpolation="nearest", cmap=cmap)
    fig.colorbar(im, ax=ax)

    classes = ["Safe (0)", "Vulnerable (1)"]
    tick_marks = np.arange(len(classes))
    ax.set_xticks(tick_marks)
    ax.set_yticks(tick_marks)
    ax.set_xticklabels(classes, fontsize=11)
    ax.set_yticklabels(classes, fontsize=11)
    ax.set_xlabel("Predicted Label", fontsize=12, labelpad=8)
    ax.set_ylabel("True Label", fontsize=12, labelpad=8)
    ax.set_title(title, fontsize=13, weight="bold", pad=12)

    # Annotate cells with counts and percentages
    cell_labels = [
        [f"TN: {tn}\n({tn/total*100:.1f}%)" if total > 0 else f"TN: {tn}",
         f"FP: {fp}\n({fp/total*100:.1f}%)" if total > 0 else f"FP: {fp}"],
        [f"FN: {fn}\n({fn/total*100:.1f}%)" if total > 0 else f"FN: {fn}",
         f"TP: {tp}\n({tp/total*100:.1f}%)" if total > 0 else f"TP: {tp}"]
    ]

    thresh = matrix.max() / 2.0 if matrix.max() > 0 else 1.0
    for i in range(2):
        for j in range(2):
            color = "white" if matrix[i, j] > thresh else "black"
            ax.text(j, i, cell_labels[i][j], ha="center", va="center", color=color, fontsize=11, weight="bold")

    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_baseline_comparison(
    models_metrics: Dict[str, Dict[str, float]],
    output_path: Path = None,
) -> None:
    """Plot grouped bar chart comparing performance across multiple baseline models.
    
    Args:
        models_metrics: Dict mapping model names to their metric dictionaries
                        (e.g., {'Logistic Regression': {'accuracy': 0.85, ...}}).
        output_path: Target filepath to save PNG image.
    """
    metrics_to_plot = ["accuracy", "precision", "recall", "f1_score", "false_negative_rate"]
    metric_display_names = ["Accuracy", "Precision", "Recall", "F1-Score", "FNR (Lower is better)"]
    
    model_names = list(models_metrics.keys())
    n_models = len(model_names)
    n_metrics = len(metrics_to_plot)

    x = np.arange(n_metrics)
    width = 0.8 / max(n_models, 1)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    for idx, (m_name, metrics) in enumerate(models_metrics.items()):
        values = [metrics.get(m, 0.0) for m in metrics_to_plot]
        offset = (idx - (n_models - 1) / 2) * width
        rects = ax.bar(x + offset, values, width, label=m_name, alpha=0.9)
        # Add value labels on top of bars
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"{height:.2f}",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Score (0.0 - 1.0)", fontsize=12)
    ax.set_title("Vulnerability Detection Baselines Comparison", fontsize=14, weight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(metric_display_names, fontsize=10)
    ax.set_ylim(0, 1.15)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=11)

    plt.tight_layout()
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
