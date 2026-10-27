"""Common internal schema and data structures for SecureCode AI.

Defines the normalized CodeSample representation across diverse vulnerability benchmarks
without fabricating missing fields.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ProvenanceType(str, Enum):
    """Origin category of the source code sample."""
    HUMAN = "human"
    AI_GENERATED = "ai_generated"
    AI_ASSISTED = "ai_assisted"
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"


class DatasetSplit(str, Enum):
    """Standardized dataset partition tags."""
    TRAIN = "train"
    VALID = "valid"
    TEST = "test"
    EXTERNAL = "external"
    SUPPLEMENTARY = "supplementary"


@dataclass
class CodeSample:
    """Unified internal data model for a single source code sample.
    
    Attributes:
        sample_id: Globally unique identifier for this sample.
        source_dataset: Origin benchmark name (e.g., 'devign', 'llmvul').
        code: Raw, unmodified function or snippet source code.
        label: 0 (non-vulnerable), 1 (vulnerable), or None if unlabeled/ambiguous.
        language: Programming language ('c', 'cpp', 'python', 'java').
        provenance: Code authorship origin ('human', 'ai_generated', 'ai_assisted', etc.).
        repository_id: Origin repository, commit, or project identifier, if known.
        cwe_id: Associated CWE identifier (e.g., 'CWE-119'), or None if unavailable.
        label_confidence: Confidence score of label (0.0 - 1.0) or None if not calculated.
        split: Partition identifier ('train', 'valid', 'test', 'external', 'supplementary').
        metadata: Dictionary holding raw benchmark-specific fields for total provenance tracking.
    """
    sample_id: str
    source_dataset: str
    code: str
    label: Optional[int] = None
    language: str = "c"
    provenance: str = ProvenanceType.UNKNOWN.value
    repository_id: Optional[str] = None
    cwe_id: Optional[str] = None
    label_confidence: Optional[float] = None
    split: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate label constraint if present
        if self.label is not None and self.label not in (0, 1):
            raise ValueError(f"Label must be 0, 1, or None; received {self.label}")
        
        # Enforce non-empty code
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("Code field must be a non-empty string.")

        # Normalize language to lowercase
        if self.language:
            self.language = self.language.lower().strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a standard Python dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeSample":
        """Construct a CodeSample from a dictionary, ensuring schema compatibility."""
        filtered_data = {
            "sample_id": str(data["sample_id"]),
            "source_dataset": str(data["source_dataset"]),
            "code": str(data["code"]),
            "label": int(data["label"]) if data.get("label") is not None else None,
            "language": str(data.get("language", "c")),
            "provenance": str(data.get("provenance", ProvenanceType.UNKNOWN.value)),
            "repository_id": str(data["repository_id"]) if data.get("repository_id") is not None else None,
            "cwe_id": str(data["cwe_id"]) if data.get("cwe_id") is not None else None,
            "label_confidence": float(data["label_confidence"]) if data.get("label_confidence") is not None else None,
            "split": str(data["split"]) if data.get("split") is not None else None,
            "metadata": dict(data.get("metadata", {})),
        }
        return cls(**filtered_data)
