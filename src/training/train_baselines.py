"""Training engine for classical machine learning baselines (TF-IDF + LR / Linear SVM).

Implements:
- Strict train-only fitting
- Validation-based model evaluation & hyperparameter tracking
- Untouched test set evaluation
- Saving models, metrics (JSON/CSV), confusion matrix figures, and logs
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.evaluation import (
    compute_vulnerability_metrics,
    plot_baseline_comparison,
    plot_confusion_matrix,
)
from src.models import TFIDFLinearSVM, TFIDFLogisticRegression
from src.utils.config import get_project_root, load_config, set_seed

logger = logging.getLogger("baseline_trainer")


def load_split_data(split_path: Path) -> Tuple[List[str], List[int]]:
    """Load classical code snippets and labels from a processed JSONL file."""
    if not split_path.exists():
        raise FileNotFoundError(f"Processed split file not found at: {split_path}")

    texts: List[str] = []
    labels: List[int] = []
    with open(split_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            # Use preprocessed classical code representation
            code = item.get("classical_code", item.get("raw_code", ""))
            label = item.get("label")
            if label is not None:
                texts.append(code)
                labels.append(int(label))
    return texts, labels


def train_and_evaluate_baselines(
    config_path: Optional[str] = None,
    dataset_name: str = "devign",
) -> Dict[str, Any]:
    """Execute complete training and evaluation pipeline for classical baselines."""
    config = load_config(config_path)
    root = get_project_root()
    seed = config.get("project", {}).get("seed", 42)
    set_seed(seed)

    # Setup directories
    results_dir = root / config.get("paths", {}).get("results_dir", "results")
    models_dir = root / config.get("paths", {}).get("models_dir", "results/models")
    metrics_dir = root / config.get("paths", {}).get("metrics_dir", "results/metrics")
    figures_dir = root / config.get("paths", {}).get("figures_dir", "results/figures")
    logs_dir = root / config.get("paths", {}).get("logs_dir", "results/logs")

    for d in [models_dir, metrics_dir, figures_dir, logs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Configure file logging
    log_file = logs_dir / "baseline_training.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger.info("=" * 60)
    logger.info("Starting SecureCode AI Classical ML Baseline Training")
    logger.info(f"Target Dataset: {dataset_name.upper()} | Seed: {seed}")
    logger.info("=" * 60)

    # Load splits
    processed_dir = root / "datasets" / "processed" / dataset_name
    X_train, y_train = load_split_data(processed_dir / "train.jsonl")
    X_valid, y_valid = load_split_data(processed_dir / "valid.jsonl")
    X_test, y_test = load_split_data(processed_dir / "test.jsonl")

    logger.info(f"Loaded Splits - Train: {len(X_train)} samples | Valid: {len(X_valid)} samples | Test: {len(X_test)} samples")
    logger.info(f"Train Class Distribution - Safe: {y_train.count(0)} | Vulnerable: {y_train.count(1)}")

    # Hyperparameters from config
    vec_params = config.get("baselines", {}).get("tfidf", {})
    lr_params = config.get("baselines", {}).get("logistic_regression", {})
    svm_params = config.get("baselines", {}).get("linear_svm", {})

    all_results: Dict[str, Any] = {}

    # =========================================================================
    # 1. TF-IDF + Logistic Regression
    # =========================================================================
    logger.info("\n--- Training Model 1: TF-IDF + Logistic Regression ---")
    lr_model = TFIDFLogisticRegression(vectorizer_params=vec_params, model_params=lr_params)
    lr_model.fit(X_train, y_train)

    # Validation evaluation (for model selection)
    val_preds_lr = lr_model.predict(X_valid)
    val_probs_lr = lr_model.predict_proba(X_valid)[:, 1]
    val_metrics_lr = compute_vulnerability_metrics(y_valid, val_preds_lr, val_probs_lr)
    logger.info(f"Logistic Regression Validation F1: {val_metrics_lr['f1_score']} | FNR: {val_metrics_lr['false_negative_rate']}")

    # Untouched test set evaluation
    test_preds_lr = lr_model.predict(X_test)
    test_probs_lr = lr_model.predict_proba(X_test)[:, 1]
    test_metrics_lr = compute_vulnerability_metrics(y_test, test_preds_lr, test_probs_lr)
    logger.info(f"Logistic Regression Test Metrics - Acc: {test_metrics_lr['accuracy']} | F1: {test_metrics_lr['f1_score']} | FNR: {test_metrics_lr['false_negative_rate']} | ROC-AUC: {test_metrics_lr['roc_auc']}")

    # Save model
    lr_path = models_dir / "tfidf_logistic_regression.joblib"
    lr_model.save(lr_path)
    logger.info(f"Saved Logistic Regression model to {lr_path.name}")

    # Plot confusion matrix
    cm_lr_path = figures_dir / "logistic_regression_cm.png"
    plot_confusion_matrix(test_metrics_lr["confusion_matrix"], title="TF-IDF + Logistic Regression (Devign Test)", output_path=cm_lr_path)

    all_results["tfidf_logistic_regression"] = {
        "model_name": "TF-IDF + Logistic Regression",
        "validation_metrics": val_metrics_lr,
        "test_metrics": test_metrics_lr,
        "model_file": str(lr_path.relative_to(root)),
        "confusion_matrix_figure": str(cm_lr_path.relative_to(root)),
    }

    # =========================================================================
    # 2. TF-IDF + Linear SVM
    # =========================================================================
    logger.info("\n--- Training Model 2: TF-IDF + Linear SVM ---")
    svm_model = TFIDFLinearSVM(vectorizer_params=vec_params, model_params=svm_params)
    svm_model.fit(X_train, y_train)

    # Validation evaluation
    val_preds_svm = svm_model.predict(X_valid)
    val_probs_svm = svm_model.predict_proba(X_valid)[:, 1]
    val_metrics_svm = compute_vulnerability_metrics(y_valid, val_preds_svm, val_probs_svm)
    logger.info(f"Linear SVM Validation F1: {val_metrics_svm['f1_score']} | FNR: {val_metrics_svm['false_negative_rate']}")

    # Untouched test set evaluation
    test_preds_svm = svm_model.predict(X_test)
    test_probs_svm = svm_model.predict_proba(X_test)[:, 1]
    test_metrics_svm = compute_vulnerability_metrics(y_test, test_preds_svm, test_probs_svm)
    logger.info(f"Linear SVM Test Metrics - Acc: {test_metrics_svm['accuracy']} | F1: {test_metrics_svm['f1_score']} | FNR: {test_metrics_svm['false_negative_rate']} | ROC-AUC: {test_metrics_svm['roc_auc']}")

    # Save model
    svm_path = models_dir / "tfidf_linear_svm.joblib"
    svm_model.save(svm_path)
    logger.info(f"Saved Linear SVM model to {svm_path.name}")

    # Plot confusion matrix
    cm_svm_path = figures_dir / "linear_svm_cm.png"
    plot_confusion_matrix(test_metrics_svm["confusion_matrix"], title="TF-IDF + Linear SVM (Devign Test)", output_path=cm_svm_path, cmap="Greens")

    all_results["tfidf_linear_svm"] = {
        "model_name": "TF-IDF + Linear SVM",
        "validation_metrics": val_metrics_svm,
        "test_metrics": test_metrics_svm,
        "model_file": str(svm_path.relative_to(root)),
        "confusion_matrix_figure": str(cm_svm_path.relative_to(root)),
    }

    # =========================================================================
    # 3. Model Comparison Plot & Metrics Summary
    # =========================================================================
    comp_plot_path = figures_dir / "baselines_comparison.png"
    plot_baseline_comparison(
        {
            "Logistic Regression": test_metrics_lr,
            "Linear SVM": test_metrics_svm,
        },
        output_path=comp_plot_path,
    )
    logger.info(f"Saved comparison figure to {comp_plot_path.name}")

    # Save metrics JSON
    metrics_json_path = metrics_dir / "baseline_metrics.json"
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    # Save metrics CSV
    summary_rows = [
        {
            "model": "TF-IDF + Logistic Regression",
            "split": "test",
            "accuracy": test_metrics_lr["accuracy"],
            "precision": test_metrics_lr["precision"],
            "recall": test_metrics_lr["recall"],
            "f1_score": test_metrics_lr["f1_score"],
            "false_negative_rate": test_metrics_lr["false_negative_rate"],
            "false_positive_rate": test_metrics_lr["false_positive_rate"],
            "roc_auc": test_metrics_lr["roc_auc"],
        },
        {
            "model": "TF-IDF + Linear SVM",
            "split": "test",
            "accuracy": test_metrics_svm["accuracy"],
            "precision": test_metrics_svm["precision"],
            "recall": test_metrics_svm["recall"],
            "f1_score": test_metrics_svm["f1_score"],
            "false_negative_rate": test_metrics_svm["false_negative_rate"],
            "false_positive_rate": test_metrics_svm["false_positive_rate"],
            "roc_auc": test_metrics_svm["roc_auc"],
        },
    ]
    df_metrics = pd.DataFrame(summary_rows)
    metrics_csv_path = metrics_dir / "baseline_metrics.csv"
    df_metrics.to_csv(metrics_csv_path, index=False)

    # Save experiment config
    exp_config_path = metrics_dir / "baseline_experiment_config.json"
    with open(exp_config_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "random_seed": seed,
                "dataset": dataset_name,
                "tfidf_params": vec_params,
                "logistic_regression_params": lr_params,
                "linear_svm_params": svm_params,
            },
            f,
            indent=2,
        )

    logger.info("\n[SUCCESS] Baseline training completed successfully.")
    logger.info(f"Metrics saved to {metrics_json_path.name} and {metrics_csv_path.name}")

    return all_results
