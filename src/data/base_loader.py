"""Base dataset loader interface and storage utilities."""

from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.schema import CodeSample


class BaseDatasetLoader(ABC):
    """Abstract base class for all benchmark dataset loaders."""

    def __init__(self, dataset_name: str, raw_dir: Optional[Path] = None, processed_dir: Optional[Path] = None):
        self.dataset_name = dataset_name
        self.raw_dir = Path(raw_dir) if raw_dir else Path(f"datasets/raw/{dataset_name}")
        self.processed_dir = Path(processed_dir) if processed_dir else Path(f"datasets/processed/{dataset_name}")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def load(self) -> List[CodeSample]:
        """Load all samples from the dataset mapped into the common CodeSample schema."""
        pass

    @abstractmethod
    def get_splits(self) -> Dict[str, List[CodeSample]]:
        """Return samples organized by split (e.g. {'train': [...], 'valid': [...], 'test': [...]})."""
        pass

    @staticmethod
    def save_jsonl(samples: List[CodeSample], output_path: Path) -> None:
        """Serialize a list of CodeSample instances to a JSONL file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")

    @staticmethod
    def load_jsonl(input_path: Path) -> List[CodeSample]:
        """Deserialize a JSONL file into a list of CodeSample instances."""
        if not input_path.exists():
            raise FileNotFoundError(f"Dataset file not found at: {input_path}")
            
        samples = []
        with open(input_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                samples.append(CodeSample.from_dict(data))
        return samples
