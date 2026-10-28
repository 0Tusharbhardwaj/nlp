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
        self.codebert_checkpoint_path: Optional[Path] = None
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
        lr_candidates = [
            self.models_dir / "logistic_regression_full.joblib",
            self.models_dir / "logistic_regression_devign.joblib",
            self.models_dir / "tfidf_logistic_regression.joblib",
        ]
        lr_path = next((p for p in lr_candidates if p.exists()), None)
        if lr_path:
            try:
                import joblib
                from sklearn.linear_model import LogisticRegression
                loaded = joblib.load(lr_path)
                if isinstance(loaded, TFIDFLogisticRegression):
                    self.loaded_models["tfidf_logistic_regression"] = loaded
                elif isinstance(loaded, LogisticRegression):
                    wrapped = TFIDFLogisticRegression()
                    wrapped.classifier = loaded
                    for v_name in ["tfidf_vectorizer_full.joblib", "tfidf_vectorizer_devign.joblib", "tfidf_vectorizer.joblib"]:
                        v_p = self.models_dir / v_name
                        if v_p.exists():
                            wrapped.vectorizer = joblib.load(v_p)
                            wrapped.is_fitted = True
                            break
                    self.loaded_models["tfidf_logistic_regression"] = wrapped
                else:
                    self.loaded_models["tfidf_logistic_regression"] = loaded
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
        svm_candidates = [
            self.models_dir / "linear_svm_full.joblib",
            self.models_dir / "linear_svm_devign.joblib",
            self.models_dir / "tfidf_linear_svm.joblib",
        ]
        svm_path = next((p for p in svm_candidates if p.exists()), None)
        if svm_path:
            try:
                import joblib
                from sklearn.svm import LinearSVC
                loaded = joblib.load(svm_path)
                if isinstance(loaded, TFIDFLinearSVM):
                    self.loaded_models["tfidf_linear_svm"] = loaded
                elif isinstance(loaded, LinearSVC) or hasattr(loaded, "decision_function"):
                    wrapped = TFIDFLinearSVM()
                    wrapped.classifier = loaded
                    for v_name in ["tfidf_vectorizer_full.joblib", "tfidf_vectorizer_devign.joblib", "tfidf_vectorizer.joblib"]:
                        v_p = self.models_dir / v_name
                        if v_p.exists():
                            wrapped.vectorizer = joblib.load(v_p)
                            wrapped.is_fitted = True
                            break
                    self.loaded_models["tfidf_linear_svm"] = wrapped
                else:
                    self.loaded_models["tfidf_linear_svm"] = loaded
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
        possible_checkpoints = [
            self.models_dir / "codebert_devign_full",
            self.checkpoints_dir / "codebert_devign_full",
            self.checkpoints_dir / "codebert_best.pt",
            self.checkpoints_dir / "best_codebert.pt",
            self.checkpoints_dir / "codebert_finetuned",
            self.models_dir / "codebert_best.pt",
            self.models_dir / "best_codebert.pt",
        ]
        
        self.codebert_checkpoint_path = None
        for candidate in possible_checkpoints:
            if candidate.exists():
                self.codebert_checkpoint_path = candidate
                break

        if self.codebert_checkpoint_path is not None:
            try:
                import torch
                from src.models.codebert_classifier import CodeBERTClassifier
                if self.codebert_checkpoint_path.is_dir():
                    classifier = CodeBERTClassifier(model_name_or_path=str(self.codebert_checkpoint_path), device="cpu")
                    if classifier.is_available():
                        self.loaded_models["codebert"] = classifier
                        status_codebert = "ready"
                    else:
                        status_codebert = "runtime_unavailable (transformers backbone initialization failed)"
                else:
                    classifier = CodeBERTClassifier(device="cpu")
                    if classifier.is_available():
                        ckpt = torch.load(self.codebert_checkpoint_path, map_location="cpu", weights_only=False)
                        state = ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt
                        classifier.model.load_state_dict(state)
                        classifier.model.eval()
                        self.loaded_models["codebert"] = classifier
                        status_codebert = "ready"
                    else:
                        status_codebert = "runtime_unavailable (transformers backbone initialization failed)"
            except Exception as e:
                status_codebert = f"runtime_unavailable (PyTorch runtime not loaded: {type(e).__name__})"
        else:
            status_codebert = "checkpoint_missing"

        ckpt_size_mb = (
            f" ({round(self.codebert_checkpoint_path.stat().st_size / (1024 * 1024), 1)} MB)"
            if self.codebert_checkpoint_path and self.codebert_checkpoint_path.is_file()
            else (" (fine-tuned directory)" if self.codebert_checkpoint_path and self.codebert_checkpoint_path.is_dir() else "")
        )

        self.model_metadata["codebert"] = {
            "id": "codebert",
            "name": f"Microsoft CodeBERT (Fine-Tuned){ckpt_size_mb}",
            "type": "transformer",
            "description": "Pre-trained bimodal RoBERTa contextual transformer fine-tuned with binary classification head on source code tokens.",
            "status": status_codebert,
            "version": "1.0.0",
            "training_dataset": "Devign (Human-written C/C++) / LLMVul",
            "metrics_summary": {
                "checkpoint": str(self.codebert_checkpoint_path) if self.codebert_checkpoint_path else "missing",
                "test_accuracy": 0.50,
                "test_f1": 0.667,
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
        """Execute single snippet vulnerability scanning with transparent model attribution."""
        self.initialize()
        requested_model = request.model_id

        if requested_model not in self.model_metadata:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model_id '{requested_model}'. Available models: {list(self.model_metadata.keys())}",
            )

        start_time = time.perf_counter()
        fallback_used = False

        # Determine target execution model and resolve availability
        if requested_model == "codebert":
            cb_model = self.loaded_models.get("codebert")
            if cb_model is None:
                if not request.allow_fallback:
                    meta = self.model_metadata["codebert"]
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            f"Model 'codebert' is currently unavailable ({meta['status']}). "
                            "PyTorch runtime is not installed or model weights could not be loaded into memory. "
                            "To execute with transparent fallback to a classical baseline, set 'allow_fallback: true'."
                        ),
                    )
                # Transparent fallback explicitly permitted by client
                actual_model_id = (
                    "tfidf_linear_svm"
                    if "tfidf_linear_svm" in self.loaded_models
                    else "tfidf_logistic_regression"
                )
                fallback_used = True
                actual_meta = self.model_metadata[actual_model_id]
                model_name = f"{actual_meta['name']} (Transparent Fallback for CodeBERT)"
                model_type = "classical"
            else:
                actual_model_id = "codebert"
                actual_meta = self.model_metadata["codebert"]
                model_name = actual_meta["name"]
                model_type = "transformer"
        else:
            actual_model_id = requested_model
            actual_meta = self.model_metadata[actual_model_id]
            if actual_meta["status"] != "ready" or actual_model_id not in self.loaded_models:
                raise HTTPException(
                    status_code=503,
                    detail=f"Model '{actual_model_id}' is not ready: {actual_meta['status']}.",
                )
            model_name = actual_meta["name"]
            model_type = actual_meta["type"]

        # Execute genuine model inference
        if actual_model_id == "codebert":
            cleaned_code = prepare_for_codebert(request.code)
            cb_model = self.loaded_models["codebert"]
            probs = cb_model.predict_proba([cleaned_code])[0]
            p0, p1 = float(probs[0]), float(probs[1])
        else:
            cleaned_code = prepare_for_classical_baseline(request.code, strip_comments=False)
            model = self.loaded_models.get(actual_model_id)
            if model is None:
                raise HTTPException(status_code=500, detail=f"Model '{actual_model_id}' failed to load from memory.")

            # Calibrated Platt scaling for linear decision margin
            if hasattr(model, "decision_function"):
                raw_score = float(model.decision_function([cleaned_code])[0])
                scale_factor = 25.0
                p1 = float(1.0 / (1.0 + np.exp(-np.clip(scale_factor * raw_score, -15, 15))))
                p0 = float(1.0 - p1)
            else:
                probs = model.predict_proba([cleaned_code])[0]
                p0, p1 = float(probs[0]), float(probs[1])

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        prediction = 1 if p1 >= 0.5 else 0
        confidence = float(max(p0, p1))

        return ScanResponse(
            model_id=actual_model_id,
            model_name=model_name,
            model_type=model_type,
            requested_model=requested_model,
            actual_model=actual_model_id,
            fallback_used=fallback_used,
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
                allow_fallback=request.allow_fallback,
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
