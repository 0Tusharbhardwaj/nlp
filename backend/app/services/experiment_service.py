"""Experiment service for parsing and serving empirical research evaluations and comparisons."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.schemas.experiments import (
    ExperimentItem,
    ExperimentResult,
    ExperimentsListResponse,
)


class ExperimentService:
    """Service to load cross-dataset and baseline benchmark results."""

    def __init__(self, metrics_dir: str = "results/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.cross_metrics_path = self.metrics_dir / "cross_dataset_metrics.json"
        self.baseline_metrics_path = self.metrics_dir / "baseline_metrics.json"

    def get_experiments(self) -> ExperimentsListResponse:
        """Load and return all empirical experiment results (E1 through E4)."""
        experiments: List[ExperimentItem] = []

        if self.cross_metrics_path.exists():
            try:
                with open(self.cross_metrics_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                exp_dict = data.get("experiments", {})
                for exp_id, exp_info in exp_dict.items():
                    results: List[ExperimentResult] = []
                    models = exp_info.get("models", {})
                    
                    for model_key, model_data in models.items():
                        if not isinstance(model_data, dict) or "metrics" not in model_data:
                            continue
                        
                        metrics = model_data.get("metrics", {})
                        cm = metrics.get("confusion_matrix", {})
                        results.append(
                            ExperimentResult(
                                experiment_id=exp_id,
                                model_name=model_data.get("model_name", model_key),
                                accuracy=float(metrics.get("accuracy", 0.0)),
                                precision=float(metrics.get("precision", 0.0)),
                                recall=float(metrics.get("recall", 0.0)),
                                f1_score=float(metrics.get("f1_score", 0.0)),
                                false_negative_rate=float(metrics.get("false_negative_rate", 0.0)),
                                roc_auc=metrics.get("roc_auc"),
                                confusion_matrix={
                                    "tn": int(cm.get("tn", 0)),
                                    "fp": int(cm.get("fp", 0)),
                                    "fn": int(cm.get("fn", 0)),
                                    "tp": int(cm.get("tp", 0)),
                                },
                            )
                        )
                    
                    description = exp_info.get("description", "")
                    if not results and models.get("status") == "skipped":
                        description += f" [Status: Skipped - {models.get('reason', '')}]"

                    experiments.append(
                        ExperimentItem(
                            experiment_id=exp_id,
                            description=description,
                            results=results,
                        )
                    )
            except Exception as e:
                experiments = []

        return ExperimentsListResponse(
            experiments=experiments,
            scientific_disclaimer=(
                "All metrics reflect empirical benchmarking across C/C++ human-authored code (Devign) and "
                "AI-generated code (LLMVul) with strict repository-disjoint cross-split partitioning."
            ),
        )

    def get_comparison(self) -> Dict[str, Any]:
        """Generate high-level research comparative summary focusing on FNR and generalization gap."""
        exp_response = self.get_experiments()
        summary = {
            "title": "Cross-Dataset Generalization & False Negative Rate (FNR) Audit",
            "thesis": (
                "Models trained exclusively on human-written code encounter domain shifts when applied "
                "to AI-generated code. Monitoring FNR (missed vulnerabilities) is essential because undetected "
                "vulnerabilities pose severe security risks in automated code generation pipelines."
            ),
            "experiments_count": len(exp_response.experiments),
            "experiments": [
                {
                    "experiment_id": exp.experiment_id,
                    "description": exp.description,
                    "models": [
                        {
                            "model_name": res.model_name,
                            "accuracy": res.accuracy,
                            "recall": res.recall,
                            "f1_score": res.f1_score,
                            "fnr": res.false_negative_rate,
                        }
                        for res in exp.results
                    ],
                }
                for exp in exp_response.experiments
            ],
        }
        return summary


experiment_service = ExperimentService()
