"""FastAPI application entry point for SecureCode AI Backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings

app = FastAPI(
    title="SecureCode AI Backend",
    description="Security and Vulnerability Detection for LLM-Generated Code REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify service status and environment."""
    return {
        "status": "healthy",
        "service": "SecureCode AI Backend",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }
