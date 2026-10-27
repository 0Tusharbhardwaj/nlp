"""Health check and system diagnostics endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.model_service import model_manager

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check():
    """Health check and runtime status report."""
    model_manager.initialize()

    # Check if GPU is available
    gpu_available = False
    try:
        import torch
        gpu_available = torch.cuda.is_available()
    except ImportError:
        pass

    loaded_count = sum(1 for m in model_manager.model_metadata.values() if m.get("status") == "ready")

    return {
        "status": "healthy",
        "service": "SecureCode AI Backend",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gpu_available": gpu_available,
        "models_ready_count": loaded_count,
        "models_registered_count": len(model_manager.model_metadata),
    }
