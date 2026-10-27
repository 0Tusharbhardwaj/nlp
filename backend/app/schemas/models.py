"""Pydantic schemas for model information and capabilities."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ModelDetails(BaseModel):
    """Detailed metadata for a registered vulnerability detection model."""

    id: str
    name: str
    type: str  # 'classical' or 'transformer'
    description: str
    status: str  # 'ready', 'checkpoint_missing'
    version: str
    training_dataset: str
    metrics_summary: Optional[Dict[str, Any]] = None


class ModelsListResponse(BaseModel):
    """Response containing available models and system default."""

    models: List[ModelDetails]
    default_model: str
