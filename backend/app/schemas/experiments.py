"""Pydantic schemas for experimental metrics and cross-dataset evaluations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ExperimentResult(BaseModel):
    """Metrics for an individual model evaluated under a specific experiment."""

    experiment_id: str
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_negative_rate: float
    roc_auc: Optional[float] = None
    confusion_matrix: Dict[str, int]


class ExperimentItem(BaseModel):
    """Complete summary of an empirical research experiment."""

    experiment_id: str
    description: str
    results: List[ExperimentResult]


class ExperimentsListResponse(BaseModel):
    """List of all completed scientific research experiments (E1-E4)."""

    experiments: List[ExperimentItem]
    scientific_disclaimer: str
