"""CodeBERT sequence classification model architecture and inference wrappers.

Uses microsoft/codebert-base with a 2-class classification head for binary vulnerability detection.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    torch = None
    nn = None
    HAS_TORCH = False


class CodeBERTClassifier:
    """Wrapper around Hugging Face CodeBERT sequence classification model.
    
    Architecture:
        - Backbone: microsoft/codebert-base (RoBERTa architecture, 12 layers, 768 hidden, 12 heads)
        - Head: Dropout + Dense(768, 768) + Tanh + Dropout + Dense(768, 2)
    """

    def __init__(
        self,
        model_name_or_path: str = "microsoft/codebert-base",
        num_labels: int = 2,
        device: Optional[str] = None,
    ):
        self.model_name_or_path = model_name_or_path
        self.num_labels = num_labels
        
        # Determine compute device
        if HAS_TORCH:
            if device is None or device == "auto":
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            else:
                self.device = torch.device(device)
        else:
            self.device = None

        self.model = None
        self.tokenizer = None
        if HAS_TORCH:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Load tokenizer and pretrained weights if transformers is installed."""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path, use_fast=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name_or_path,
                num_labels=self.num_labels,
            )
            self.model.to(self.device)
        except Exception as e:
            # Fallback for environments without downloaded weights or without transformers
            self.tokenizer = None
            self.model = None

    def is_available(self) -> bool:
        """Check if model and tokenizer are loaded and available for execution."""
        return self.model is not None and self.tokenizer is not None

    def predict(self, code_snippets: List[str], max_length: int = 512, batch_size: int = 16) -> np.ndarray:
        """Run batch inference and return predicted binary classes (0 or 1)."""
        probs = self.predict_proba(code_snippets, max_length=max_length, batch_size=batch_size)
        return (probs[:, 1] >= 0.5).astype(int)

    def predict_proba(self, code_snippets: List[str], max_length: int = 512, batch_size: int = 16):
        """Run batch inference and return class probabilities [P(safe), P(vulnerable)]."""
        import numpy as np
        if not self.is_available():
            raise RuntimeError("CodeBERT model weights are not loaded. Cannot run inference.")

        self.model.eval()
        all_probs = []

        with torch.no_grad():
            for i in range(0, len(code_snippets), batch_size):
                batch = code_snippets[i : i + batch_size]
                inputs = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=max_length,
                    return_tensors="pt",
                ).to(self.device)

                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1).cpu().numpy()
                all_probs.append(probs)

        return np.vstack(all_probs)

    def save_pretrained(self, save_directory: Union[str, Path]) -> None:
        """Save model weights, configuration, and tokenizer."""
        if not self.is_available():
            raise RuntimeError("No model loaded to save.")
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(str(save_path))
        self.tokenizer.save_pretrained(str(save_path))

    @classmethod
    def from_pretrained(cls, save_directory: Union[str, Path], device: Optional[str] = None) -> "CodeBERTClassifier":
        """Load fine-tuned model and tokenizer from directory."""
        return cls(model_name_or_path=str(save_directory), device=device)
