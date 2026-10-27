"""Consolidated API router aggregating all version 1 endpoints."""

from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.models import router as models_router
from backend.app.api.scan import router as scan_router
from backend.app.api.datasets import router as datasets_router
from backend.app.api.experiments import router as experiments_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(scan_router)
api_router.include_router(datasets_router)
api_router.include_router(experiments_router)
