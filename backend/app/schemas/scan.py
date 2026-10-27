"""Pydantic schemas for single and batch vulnerability scanning."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ScanRequest(BaseModel):
    """Payload for scanning a single source code snippet."""

    code: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Source code snippet to analyze for security vulnerabilities.",
        examples=["static void copy_data(char *dst, const char *src) { strcpy(dst, src); }"],
    )
    model_id: str = Field(
        default="tfidf_logistic_regression",
        description="Identifier of model to use: 'tfidf_logistic_regression', 'tfidf_linear_svm', or 'codebert'.",
    )
    language: str = Field(
        default="c",
        description="Programming language of the snippet ('c', 'cpp', 'python').",
    )

    @field_validator("code")
    @classmethod
    def validate_code_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Source code snippet cannot be empty or purely whitespace.")
        return v


class ScanResponse(BaseModel):
    """Result payload for source-code vulnerability scanning."""

    model_id: str
    model_name: str
    model_type: str
    is_vulnerable: bool
    prediction: int = Field(..., description="0 = Safe, 1 = Vulnerable")
    confidence: float = Field(..., description="Probability of predicted class (0.0 to 1.0)")
    probabilities: Dict[str, float] = Field(..., description="Class probabilities: {'safe': p0, 'vulnerable': p1}")
    inference_time_ms: float = Field(..., description="Inference latency in milliseconds")
    disclaimer: str = Field(
        default="Notice: This output is a machine-learning statistical prediction, not mathematical proof or formal verification of a vulnerability."
    )


class BatchScanItem(BaseModel):
    """Individual item within a batch scan request."""

    id: Optional[str] = None
    code: str = Field(..., min_length=1, max_length=50000)
    language: Optional[str] = "c"

    @field_validator("code")
    @classmethod
    def validate_code_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Code snippet cannot be empty.")
        return v


class BatchScanRequest(BaseModel):
    """Payload for scanning multiple source code snippets concurrently."""

    items: List[BatchScanItem] = Field(..., min_length=1, max_length=100)
    model_id: str = Field(default="tfidf_logistic_regression")


class BatchScanResponse(BaseModel):
    """Result payload for batch source-code vulnerability scanning."""

    model_id: str
    total_processed: int
    total_time_ms: float
    results: List[ScanResponse]
