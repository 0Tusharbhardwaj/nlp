"""Evaluation metrics computation for binary vulnerability classification.

Implements:
- Accuracy, Precision, Recall, F1-Score
- False Negative Rate (FNR = FN / (TP + FN) = 1 - Recall)
- ROC-AUC (when probabilities or decision scores are provided)
- Confusion matrix extraction (raw counts and normalized rates)
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_vulnerability_metrics(
    y_true: Union[List[int], np.ndarray],
    y_pred: Union[List[int], np.ndarray],
    y_scores: Optional[Union[List[float], np.ndarray]] = None,
) -> Dict[str, Any]:
    """Compute complete scientific vulnerability detection metrics.
    
    Args:
        y_true: Ground truth binary labels (0 = safe, 1 = vulnerable).
        y_pred: Predicted binary labels (0 = safe, 1 = vulnerable).
        y_scores: Predicted probabilities or decision values for class 1 (optional, for ROC-AUC).
        
    Returns:
        Dictionary containing all evaluation metrics and confusion matrix values.
    """
    y_true = np.array(y_true, dtype=int)
    y_pred = np.array(y_pred, dtype=int)

    # Confusion matrix extraction
    # labels=[0, 1] ensures 2x2 shape even if a batch contains only one class
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Core classification metrics
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    rec = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))

    # False Negative Rate: FNR = FN / (FN + TP)
    actual_positives = tp + fn
    fnr = float(fn / actual_positives) if actual_positives > 0 else 0.0

    # False Positive Rate: FPR = FP / (FP + TN)
    actual_negatives = tn + fp
    fpr = float(fp / actual_negatives) if actual_negatives > 0 else 0.0

    # ROC-AUC calculation
    roc_auc = None
    if y_scores is not None:
        try:
            # ROC-AUC requires at least one positive and one negative sample
            if len(np.unique(y_true)) > 1:
                roc_auc = float(roc_auc_score(y_true, y_scores))
        except Exception:
            roc_auc = None

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "false_negative_rate": round(fnr, 4),
        "false_positive_rate": round(fpr, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else None,
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "sample_counts": {
            "total": int(len(y_true)),
            "actual_vulnerable (1)": int(actual_positives),
            "actual_safe (0)": int(actual_negatives),
            "predicted_vulnerable (1)": int(tp + fp),
            "predicted_safe (0)": int(tn + fn),
        },
    }
