"""CLI script to run CodeBERT fine-tuning locally or on a GPU server."""

import argparse
from pathlib import Path
import sys

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.training import train_codebert_model


def main():
    parser = argparse.ArgumentParser(description="Fine-tune CodeBERT on vulnerability detection benchmarks.")
    parser.add_argument("--config", type=str, default="configs/base.yaml", help="Path to base config YAML.")
    parser.add_argument("--dataset", type=str, default="devign", help="Target dataset name.")
    parser.add_argument("--checkpoints", type=str, default=None, help="Directory to store epoch checkpoints.")
    parser.add_argument("--output", type=str, default=None, help="Directory to store final best model.")
    args = parser.parse_args()

    results = train_codebert_model(
        config_path=args.config,
        dataset_name=args.dataset,
        checkpoint_dir=args.checkpoints,
        output_dir=args.output,
    )

    if results.get("status") == "skipped":
        print(f"\n[NOTICE] Training skipped: {results.get('reason')}")
        print("Note: CodeBERT requires PyTorch and Transformers with GPU acceleration. Use notebooks/01_codebert_finetuning.ipynb on Google Colab.")
    else:
        m = results.get("test_metrics", {})
        print("\n--- CodeBERT Test Evaluation Summary ---")
        print(f"Accuracy: {m.get('accuracy')} | F1-Score: {m.get('f1_score')} | Recall: {m.get('recall')} | FNR: {m.get('false_negative_rate')} | ROC-AUC: {m.get('roc_auc')}")


if __name__ == "__main__":
    main()
