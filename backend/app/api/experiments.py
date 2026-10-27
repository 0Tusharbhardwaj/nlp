"""API endpoints for empirical research experiments and cross-dataset evaluations."""

from typing import Any, Dict
from fastapi import APIRouter
from backend.app.schemas.experiments import ExperimentsListResponse
from backend.app.services.experiment_service import experiment_service

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("", response_model=ExperimentsListResponse)
async def list_experiments() -> ExperimentsListResponse:
    """Retrieve all empirical experiments (E1 to E4) and their performance metrics."""
    return experiment_service.get_experiments()


@router.get("/comparison", response_model=Dict[str, Any])
async def get_comparison() -> Dict[str, Any]:
    """Retrieve cross-dataset generalization comparison and False Negative Rate (FNR) audit."""
    return experiment_service.get_comparison()
