"""API endpoints for source-code vulnerability scanning."""

from fastapi import APIRouter
from backend.app.schemas.scan import (
    BatchScanRequest,
    BatchScanResponse,
    ScanRequest,
    ScanResponse,
)
from backend.app.services.model_service import model_manager

router = APIRouter(prefix="/scan", tags=["Scanning"])


@router.post("", response_model=ScanResponse)
async def scan_code(request: ScanRequest) -> ScanResponse:
    """Analyze a single source code snippet for security vulnerabilities."""
    return model_manager.scan(request)


@router.post("/batch", response_model=BatchScanResponse)
async def scan_code_batch(request: BatchScanRequest) -> BatchScanResponse:
    """Analyze multiple source code snippets concurrently for vulnerabilities."""
    return model_manager.scan_batch(request)
