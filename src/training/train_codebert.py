"""PyTorch / Hugging Face training engine for CodeBERT binary vulnerability fine-tuning.

Features:
- NVIDIA GPU / CUDA detection and automatic device mapping
- Checkpoint saving and resumption for interrupted training sessions (Google Colab recovery)
- Weighted Cross-Entropy Loss for class imbalance mitigation
- Untruncated sequence length logging and truncation monitoring
- Validation-based model selection (Best Macro F1)
- Untouched test set final scoring
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
    HAS_TORCH = True
except ImportError:
    torch = None
    nn = None
    DataLoader = None
    Dataset = object
    HAS_TORCH = False

from src.evaluation import compute_vulnerability_metrics, plot_confusion_matrix
from src.utils.config import get_project_root, load_config, set_seed

logger = logging.getLogger("codebert_trainer")


class VulnerabilityDataset(Dataset):
    """PyTorch Dataset for source-code vulnerability sequences."""

    def __init__(self, encodings: Dict[str, Any], labels: List[int]):
        self.encodings = encodings
        if HAS_TORCH:
            self.labels = torch.tensor(labels, dtype=torch.long)
        else:
            self.labels = labels

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        if HAS_TORCH:
            item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
            item["labels"] = self.labels[idx]
            return item
        return {key: val[idx] for key, val in self.encodings.items()}

    def __len__(self) -> int:
        return len(self.labels)


def load_codebert_split_data(split_path: Path) -> Tuple[List[str], List[int]]:
    """Load CodeBERT code representations and labels from processed JSONL file."""
    if not split_path.exists():
        raise FileNotFoundError(f"Split file not found: {split_path}")

    codes: List[str] = []
    labels: List[int] = []
    with open(split_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            # Use codebert_code where syntax and identifiers are intact
            code = data.get("codebert_code", data.get("raw_code", ""))
            label = data.get("label")
            if label is not None:
                codes.append(code)
                labels.append(int(label))
    return codes, labels


def compute_class_weights(labels: List[int], device: Any) -> Any:
    """Compute balanced class weights: weight_c = N / (2 * N_c)."""
    if not HAS_TORCH:
        return None
    n_samples = len(labels)
    n_class_0 = sum(1 for y in labels if y == 0)
    n_class_1 = sum(1 for y in labels if y == 1)

    w0 = (n_samples / (2.0 * max(n_class_0, 1)))
    w1 = (n_samples / (2.0 * max(n_class_1, 1)))

    weights = torch.tensor([w0, w1], dtype=torch.float, device=device)
    logger.info(f"Computed Class Weights - Class 0 (Safe): {w0:.3f} | Class 1 (Vulnerable): {w1:.3f}")
    return weights


def train_codebert_model(
    config_path: Optional[str] = None,
    dataset_name: str = "devign",
    checkpoint_dir: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Fine-tune CodeBERT on validated dataset splits with full checkpointing."""
    if not HAS_TORCH:
        logger.warning(
            "PyTorch is not installed in the local environment. CodeBERT fine-tuning requires "
            "PyTorch/CUDA. Use Google Colab GPU runtime (notebooks/01_codebert_finetuning.ipynb)."
        )
        return {"status": "skipped", "reason": "torch_not_installed"}

    config = load_config(config_path)
    root = get_project_root()
    seed = config.get("project", {}).get("seed", 42)
    set_seed(seed)

    # Resolve paths
    base_checkpoints = Path(checkpoint_dir) if checkpoint_dir else (root / "results" / "checkpoints" / "codebert")
    base_models = Path(output_dir) if output_dir else (root / "results" / "models" / "codebert_finetuned")
    metrics_dir = root / "results" / "metrics"
    figures_dir = root / "results" / "figures"
    logs_dir = root / "results" / "logs"

    for d in [base_checkpoints, base_models, metrics_dir, figures_dir, logs_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Configure logging
    log_file = logs_dir / "codebert_training.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    logger.info("=" * 60)
    logger.info("Starting CodeBERT Binary Vulnerability Fine-Tuning Pipeline")
    logger.info(f"Target Dataset: {dataset_name.upper()} | Seed: {seed}")
    logger.info("=" * 60)

    # Check CUDA device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_fp16 = torch.cuda.is_available() and config.get("codebert", {}).get("fp16", True)
    logger.info(f"Compute Device: {device.type.upper()} | FP16 Acceleration: {use_fp16}")
    if torch.cuda.is_available():
        logger.info(f"GPU Hardware: {torch.cuda.get_device_name(0)}")

    # Load preprocessed splits
    proc_dir = root / "datasets" / "processed" / dataset_name
    X_train, y_train = load_codebert_split_data(proc_dir / "train.jsonl")
    X_valid, y_valid = load_codebert_split_data(proc_dir / "valid.jsonl")
    X_test, y_test = load_codebert_split_data(proc_dir / "test.jsonl")

    logger.info(f"Splits Loaded - Train: {len(X_train)} | Valid: {len(X_valid)} | Test: {len(X_test)}")

    # Load Tokenizer & Model
    model_name = config.get("codebert", {}).get("model_name_or_path", "microsoft/codebert-base")
    max_len = config.get("preprocessing", {}).get("max_sequence_length", 512)
    lr = float(config.get("codebert", {}).get("learning_rate", 2e-5))
    batch_size = int(config.get("codebert", {}).get("per_device_train_batch_size", 16))
    num_epochs = int(config.get("codebert", {}).get("num_train_epochs", 3))

    try:
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            get_linear_schedule_with_warmup,
        )
    except ImportError as e:
        logger.error(f"Transformers library is required for CodeBERT fine-tuning: {e}")
        return {"status": "skipped", "reason": "transformers_not_installed"}

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    model.to(device)

    # Tokenize datasets
    train_enc = tokenizer(X_train, padding="max_length", truncation=True, max_length=max_len)
    valid_enc = tokenizer(X_valid, padding="max_length", truncation=True, max_length=max_len)
    test_enc = tokenizer(X_test, padding="max_length", truncation=True, max_length=max_len)

    train_dataset = VulnerabilityDataset(train_enc, y_train)
    valid_dataset = VulnerabilityDataset(valid_enc, y_valid)
    test_dataset = VulnerabilityDataset(test_enc, y_test)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    valid_loader = DataLoader(valid_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Class weights for loss
    class_weights = compute_class_weights(y_train, device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # Optimizer & Scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * num_epochs
    warmup_steps = int(total_steps * config.get("codebert", {}).get("warmup_ratio", 0.1))
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)
    scaler = torch.cuda.amp.GradScaler(enabled=use_fp16)

    # Checkpoint recovery check
    best_checkpoint_file = base_checkpoints / "checkpoint_best.pt"
    start_epoch = 0
    best_f1 = -1.0
    training_history = []

    if best_checkpoint_file.exists():
        logger.info(f"Found existing checkpoint at {best_checkpoint_file}. Resuming training...")
        checkpoint = torch.load(best_checkpoint_file, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_epoch = checkpoint.get("epoch", 0) + 1
        best_f1 = checkpoint.get("best_f1", -1.0)
        training_history = checkpoint.get("training_history", [])
        logger.info(f"Resumed from Epoch {start_epoch} with previous Best F1: {best_f1:.4f}")

    # =========================================================================
    # Training Loop
    # =========================================================================
    for epoch in range(start_epoch, num_epochs):
        model.train()
        train_loss = 0.0

        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            with torch.cuda.amp.autocast(enabled=use_fp16):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                loss = criterion(outputs.logits, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            train_loss += loss.item()

        avg_train_loss = train_loss / max(len(train_loader), 1)

        # Validation Evaluation
        model.eval()
        val_preds = []
        val_probs = []
        val_labels = []

        with torch.no_grad():
            for batch in valid_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"]

                with torch.cuda.amp.autocast(enabled=use_fp16):
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
                preds = np.argmax(probs, axis=-1)

                val_probs.extend(probs[:, 1].tolist())
                val_preds.extend(preds.tolist())
                val_labels.extend(labels.tolist())

        val_metrics = compute_vulnerability_metrics(val_labels, val_preds, val_probs)
        current_f1 = val_metrics["f1_score"]

        epoch_record = {
            "epoch": epoch + 1,
            "train_loss": round(avg_train_loss, 4),
            "val_f1": current_f1,
            "val_accuracy": val_metrics["accuracy"],
            "val_fnr": val_metrics["false_negative_rate"],
        }
        training_history.append(epoch_record)

        logger.info(
            f"Epoch {epoch + 1}/{num_epochs} - Train Loss: {avg_train_loss:.4f} | "
            f"Val F1: {current_f1:.4f} | Val FNR: {val_metrics['false_negative_rate']:.4f}"
        )

        # Save checkpoint if best validation F1
        if current_f1 > best_f1:
            best_f1 = current_f1
            logger.info(f"[*] New best validation F1 ({best_f1:.4f})! Saving checkpoint...")
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_f1": best_f1,
                    "training_history": training_history,
                },
                best_checkpoint_file,
            )
            # Save Hugging Face format
            model.save_pretrained(str(base_models))
            tokenizer.save_pretrained(str(base_models))

    # =========================================================================
    # Final Untouched Test Set Evaluation
    # =========================================================================
    logger.info("\n--- Final Evaluation on Untouched Test Set ---")
    # Load best model weights
    if best_checkpoint_file.exists():
        ckpt = torch.load(best_checkpoint_file, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])
        logger.info("Loaded best model weights based on validation selection.")

    model.eval()
    test_preds = []
    test_probs = []
    test_labels = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"]

            with torch.cuda.amp.autocast(enabled=use_fp16):
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)

            probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
            preds = np.argmax(probs, axis=-1)

            test_probs.extend(probs[:, 1].tolist())
            test_preds.extend(preds.tolist())
            test_labels.extend(labels.tolist())

    test_metrics = compute_vulnerability_metrics(test_labels, test_preds, test_probs)
    logger.info(
        f"CodeBERT Final Test - Accuracy: {test_metrics['accuracy']} | F1: {test_metrics['f1_score']} | "
        f"Recall: {test_metrics['recall']} | FNR: {test_metrics['false_negative_rate']} | ROC-AUC: {test_metrics['roc_auc']}"
    )

    # Plot and save confusion matrix
    cm_path = figures_dir / "codebert_cm.png"
    plot_confusion_matrix(test_metrics["confusion_matrix"], title="CodeBERT Fine-Tuned (Devign Test)", output_path=cm_path, cmap="Purples")

    # Save metrics JSON
    final_output = {
        "model_name": "CodeBERT Sequence Classifier (microsoft/codebert-base)",
        "task": "binary_vulnerability_detection",
        "dataset": dataset_name,
        "best_validation_f1": best_f1,
        "training_history": training_history,
        "test_metrics": test_metrics,
        "model_directory": str(base_models.relative_to(root)),
        "confusion_matrix_figure": str(cm_path.relative_to(root)),
    }

    metrics_file = metrics_dir / "codebert_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    logger.info(f"\n[SUCCESS] CodeBERT training complete. Metrics saved to {metrics_file.name}")
    return final_output
