"""FastAPI application entry point for SecureCode AI Backend."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.services.model_service import model_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    # Pre-load trained models into memory on server boot
    model_manager.initialize()
    yield
    # Teardown logic if needed on graceful shutdown


app = FastAPI(
    title="SecureCode AI Backend",
    description="Security and Vulnerability Detection for LLM-Generated Code REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount consolidated v1 API router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["System"])
async def root():
    """Root endpoint providing service information and API documentation links."""
    return {
        "service": "SecureCode AI Backend",
        "description": "Security and Vulnerability Detection for LLM-Generated Code",
        "version": "1.0.0",
        "api_v1": settings.API_PREFIX,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["System"])
async def root_health_check():
    """Top-level health check endpoint."""
    return {
        "status": "healthy",
        "service": "SecureCode AI Backend",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }
