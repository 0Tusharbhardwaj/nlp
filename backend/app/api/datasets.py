"""API endpoints for inspecting benchmark datasets and profiling metrics."""

from fastapi import APIRouter
from backend.app.schemas.datasets import DatasetsListResponse
from backend.app.services.dataset_service import dataset_service

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("", response_model=DatasetsListResponse)
async def list_datasets() -> DatasetsListResponse:
    """Retrieve all benchmark datasets, language scopes, and quality audit summaries."""
    return dataset_service.get_all_datasets()
