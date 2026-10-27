"""CodeXGLUE / Devign vulnerability dataset loader.

Reference:
- Microsoft CodeXGLUE (Code-Code Defect Detection)
- Zhou et al., "Devign: Effective Vulnerability Identification by Learning
  Comprehensive Program Semantics via Graph Neural Networks", NeurIPS 2019.
- Hugging Face: google/code_x_glue_cc_defect_detection
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.base_loader import BaseDatasetLoader
from src.data.schema import CodeSample, DatasetSplit, ProvenanceType


class DevignDatasetLoader(BaseDatasetLoader):
    """Loader for the CodeXGLUE/Devign C/C++ defect detection benchmark."""

    OFFICIAL_SPLITS = [DatasetSplit.TRAIN.value, DatasetSplit.VALID.value, DatasetSplit.TEST.value]

    def __init__(self, raw_dir: Optional[Path] = None, processed_dir: Optional[Path] = None):
        super().__init__("devign", raw_dir, processed_dir)

    def load_from_raw_records(self, records: List[Dict[str, Any]], split: str = "train") -> List[CodeSample]:
        """Convert raw CodeXGLUE/Devign dictionary records to CodeSample instances.
        
        Raw Schema:
            - id / idx: int
            - func: str (C source code)
            - target: int/bool (0 for non-vulnerable, 1 for vulnerable)
            - project: str (e.g. 'qemu', 'ffmpeg')
            - commit_id: str (commit hash)
        """
        samples: List[CodeSample] = []
        for record in records:
            raw_id = record.get("id", record.get("idx", ""))
            func_code = record.get("func", "").strip()
            if not func_code:
                continue

            target_val = record.get("target")
            if target_val is not None:
                label = 1 if int(target_val) == 1 else 0
            else:
                label = None

            sample = CodeSample(
                sample_id=f"devign_{split}_{raw_id}",
                source_dataset="devign",
                code=func_code,
                label=label,
                language="c",
                provenance=ProvenanceType.HUMAN.value,
                repository_id=record.get("project"),
                cwe_id=None,  # Devign benchmark does not supply ground-truth CWE numbers in raw form
                label_confidence=1.0 if label is not None else None,
                split=split,
                metadata={
                    "original_id": raw_id,
                    "commit_id": record.get("commit_id"),
                    "project": record.get("project"),
                },
            )
            samples.append(sample)
        return samples

    def load(self) -> List[CodeSample]:
        """Load all splits and return as a combined list."""
        all_samples: List[CodeSample] = []
        splits = self.get_splits()
        for s_list in splits.values():
            all_samples.extend(s_list)
        return all_samples

    def get_splits(self) -> Dict[str, List[CodeSample]]:
        """Load samples partitioned by official splits (train, valid, test)."""
        splits: Dict[str, List[CodeSample]] = {s: [] for s in self.OFFICIAL_SPLITS}

        # Check for local files in raw_dir
        for split in self.OFFICIAL_SPLITS:
            raw_file = self.raw_dir / f"{split}.jsonl"
            if raw_file.exists():
                records = []
                with open(raw_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            records.append(json.loads(line))
                splits[split] = self.load_from_raw_records(records, split=split)

        return splits

    def save_raw_splits(self, split_records: Dict[str, List[Dict[str, Any]]]) -> None:
        """Save raw dictionary splits to raw_dir as JSONL."""
        for split, records in split_records.items():
            path = self.raw_dir / f"{split}.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
