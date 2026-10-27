"""Model management service for loading, caching, and running vulnerability inference."""

from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import numpy as np
from fastapi import HTTPException

from backend.app.schemas.models import ModelDetails, ModelsListResponse
from backend.app.schemas.scan import (
    BatchScanItem,
    BatchScanRequest,
    BatchScanResponse,
    ScanRequest,
    ScanResponse,
)
from src.models.baseline_tfidf import TFIDFLinearSVM, TFIDFLogisticRegression
from src.preprocessing.safe_cleaner import prepare_for_classical_baseline, prepare_for_codebert


class ModelManager:
    """Singleton service to load models once and execute low-latency inference."""

    _instance: Optional["ModelManager"] = None

    def __init__(self, models_dir: str = "results/models", checkpoints_dir: str = "results/checkpoints"):
        self.models_dir = Path(models_dir)
        self.checkpoints_dir = Path(checkpoints_dir)
        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self._is_initialized = False

    @classmethod
    def get_instance(cls) -> "ModelManager":
        """Access singleton ModelManager instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self) -> None:
        """Load available models from disk into memory."""
        if self._is_initialized:
            return

        # 1. TF-IDF + Logistic Regression
        lr_path = self.models_dir / "tfidf_logistic_regression.joblib"
        if lr_path.exists():
            try:
                self.loaded_models["tfidf_logistic_regression"] = TFIDFLogisticRegression.load(lr_path)
                status_lr = "ready"
            except Exception as e:
                status_lr = f"load_failed: {str(e)}"
        else:
            status_lr = "checkpoint_missing"

        self.model_metadata["tfidf_logistic_regression"] = {
            "id": "tfidf_logistic_regression",
            "name": "TF-IDF + Logistic Regression",
            "type": "classical",
            "description": "N-gram lexical TF-IDF feature extractor paired with balanced Logistic Regression classifier.",
            "status": status_lr,
            "version": "1.0.0",
            "training_dataset": "Devign (Human-written C/C++)",
            "metrics_summary": {
                "test_accuracy": 0.50,
                "test_f1": 0.667,
                "test_recall": 1.00,
                "false_negative_rate": 0.00,
            },
        }

        # 2. TF-IDF + Linear SVM
        svm_path = self.models_dir / "tfidf_linear_svm.joblib"
        if svm_path.exists():
            try:
                self.loaded_models["tfidf_linear_svm"] = TFIDFLinearSVM.load(svm_path)
                status_svm = "ready"
            except Exception as e:
                status_svm = f"load_failed: {str(e)}"
        else:
            status_svm = "checkpoint_missing"

        self.model_metadata["tfidf_linear_svm"] = {
            "id": "tfidf_linear_svm",
            "name": "TF-IDF + Linear SVM",
            "type": "classical",
            "description": "N-gram lexical TF-IDF feature extractor with balanced Linear Support Vector Machine (LinearSVC) and Platt scaling.",
            "status": status_svm,
            "version": "1.0.0",
            "training_dataset": "Devign (Human-written C/C++)",
            "metrics_summary": {
                "test_accuracy": 0.50,
                "test_f1": 0.667,
                "test_recall": 1.00,
                "false_negative_rate": 0.00,
            },
        }

        # 3. Microsoft CodeBERT
        codebert_checkpoint = self.checkpoints_dir / "best_codebert.pt"
        codebert_hf_dir = self.checkpoints_dir / "codebert_finetuned"
        if codebert_checkpoint.exists() or codebert_hf_dir.exists():
            status_codebert = "ready"
        else:
            status_codebert = "checkpoint_missing"

        self.model_metadata["codebert"] = {
            "id": "codebert",
            "name": "Microsoft CodeBERT (Fine-Tuned)",
            "type": "transformer",
            "description": "Pre-trained bimodal RoBERTa contextual transformer fine-tuned with binary classification head on source code tokens.",
            "status": status_codebert,
            "version": "1.0.0",
            "training_dataset": "Devign (Human-written C/C++) / LLMVul",
            "metrics_summary": {
                "note": "Train via Colab GPU notebook: notebooks/01_codebert_finetuning.ipynb",
            },
        }

        self._is_initialized = True

    def list_models(self) -> ModelsListResponse:
        """List all registered models and their readiness status."""
        self.initialize()
        models = [ModelDetails(**meta) for meta in self.model_metadata.values()]
        return ModelsListResponse(
            models=models,
            default_model="tfidf_logistic_regression",
        )

    def get_model_details(self, model_id: str) -> ModelDetails:
        """Get metadata for a specific model."""
        self.initialize()
        if model_id not in self.model_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_id}' is not recognized. Valid options: {list(self.model_metadata.keys())}",
            )
        return ModelDetails(**self.model_metadata[model_id])

    def scan(self, request: ScanRequest) -> ScanResponse:
        """Execute single snippet vulnerability scanning."""
        self.initialize()
        model_id = request.model_id

        if model_id not in self.model_metadata:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model_id '{model_id}'. Available models: {list(self.model_metadata.keys())}",
            )

        meta = self.model_metadata[model_id]

        if meta["status"] != "ready":
            if model_id == "codebert":
                raise HTTPException(
                    status_code=503,
                    detail="CodeBERT checkpoint is not loaded. Train CodeBERT using the Colab GPU notebook (notebooks/01_codebert_finetuning.ipynb) and place weights in results/checkpoints/.",
                )
            raise HTTPException(
                status_code=503,
                detail=f"Model '{model_id}' is not ready: {meta['status']}.",
            )

        model = self.loaded_models.get(model_id)
        if model is None:
            raise HTTPException(status_code=500, detail=f"Model '{model_id}' failed to load from memory.")

        # Clean code
        start_time = time.perf_counter()
        if meta["type"] == "classical":
            cleaned_code = prepare_for_classical_baseline(request.code, strip_comments=False)
            probs = model.predict_proba([cleaned_code])[0]
        else:
            cleaned_code = prepare_for_codebert(request.code)
            probs = model.predict_proba([cleaned_code])[0]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        p0 = float(probs[0])
        p1 = float(probs[1])
        prediction = 1 if p1 >= 0.5 else 0
        confidence = float(max(p0, p1))

        return ScanResponse(
            model_id=model_id,
            model_name=meta["name"],
            model_type=meta["type"],
            is_vulnerable=(prediction == 1),
            prediction=prediction,
            confidence=round(confidence, 4),
            probabilities={"safe": round(p0, 4), "vulnerable": round(p1, 4)},
            inference_time_ms=round(elapsed_ms, 2),
            disclaimer="Notice: This output is a machine-learning statistical prediction, not mathematical proof or formal verification of a vulnerability.",
        )

    def scan_batch(self, request: BatchScanRequest) -> BatchScanResponse:
        """Execute batch vulnerability scanning on a list of code snippets."""
        self.initialize()
        start_batch_time = time.perf_counter()

        results: List[ScanResponse] = []
        for item in request.items:
            single_req = ScanRequest(
                code=item.code,
                model_id=request.model_id,
                language=item.language or "c",
            )
            results.append(self.scan(single_req))

        total_ms = (time.perf_counter() - start_batch_time) * 1000.0

        return BatchScanResponse(
            model_id=request.model_id,
            total_processed=len(results),
            total_time_ms=round(total_ms, 2),
            results=results,
        )


model_manager = ModelManager.get_instance()
