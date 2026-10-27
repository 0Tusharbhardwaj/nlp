"""API endpoints for inspecting available vulnerability detection models."""

from fastapi import APIRouter
from backend.app.schemas.models import ModelDetails, ModelsListResponse
from backend.app.services.model_service import model_manager

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=ModelsListResponse)
async def list_models() -> ModelsListResponse:
    """Retrieve all registered vulnerability detection models and their statuses."""
    return model_manager.list_models()


@router.get("/{model_id}", response_model=ModelDetails)
async def get_model(model_id: str) -> ModelDetails:
    """Retrieve detailed metadata and capabilities for a specific model."""
    return model_manager.get_model_details(model_id)
