"""CLI script to train and evaluate classical machine learning baselines."""

import argparse
from pathlib import Path
import sys

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.training import train_and_evaluate_baselines


def main():
    parser = argparse.ArgumentParser(description="Train classical ML baselines (TF-IDF + LR/SVM).")
    parser.add_argument("--config", type=str, default="configs/base.yaml", help="Path to base config YAML.")
    parser.add_argument("--dataset", type=str, default="devign", help="Target dataset name.")
    args = parser.parse_args()

    results = train_and_evaluate_baselines(config_path=args.config, dataset_name=args.dataset)
    print("\n--- Summary of Test Metrics ---")
    for key, data in results.items():
        m = data["test_metrics"]
        print(f"{data['model_name']}: Accuracy = {m['accuracy']}, F1 = {m['f1_score']}, Recall = {m['recall']}, FNR = {m['false_negative_rate']}, ROC-AUC = {m['roc_auc']}")


if __name__ == "__main__":
    main()
