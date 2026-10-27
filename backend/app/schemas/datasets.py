"""Pydantic schemas for dataset information and research profiling."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DatasetInfo(BaseModel):
    """Metadata and statistics for a registered vulnerability benchmark."""

    id: str
    name: str
    language: str
    provenance: str
    granularity: str
    vulnerability_rate: Optional[float] = None
    role: str
    status: str
    samples_count: Dict[str, int]


class DatasetsListResponse(BaseModel):
    """List of all evaluated benchmark datasets and their profiling status."""

    total_datasets: int
    datasets: List[DatasetInfo]
