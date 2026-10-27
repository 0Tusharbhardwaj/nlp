"""SECODEPLT benchmark dataset loader.

Reference:
- "SeCodePLT: A Unified Platform for Evaluating the Security of Code GenAI",
  arXiv:2410.11096 (NeurIPS 2024 / UCSB-SURFI).
- Hugging Face: UCSB-SURFI/SeCodePLT
- GitHub: ucsb-mlsec/SeCodePLT
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.base_loader import BaseDatasetLoader
from src.data.schema import CodeSample, DatasetSplit, ProvenanceType


class SeCodePLTDatasetLoader(BaseDatasetLoader):
    """Loader for the SECODEPLT benchmark, focusing on the Vulnerability Detection subtask."""

    def __init__(self, raw_dir: Optional[Path] = None, processed_dir: Optional[Path] = None):
        super().__init__("secodeplt", raw_dir, processed_dir)

    def load_from_raw_records(self, records: List[Dict[str, Any]], split: str = DatasetSplit.SUPPLEMENTARY.value) -> List[CodeSample]:
        """Convert raw SECODEPLT records to CodeSample instances.
        
        Raw Schema (Vulnerability Detection subtask):
            - task_id / id: str
            - code / prompt_code: str
            - is_vulnerable / label / target: bool or int (1: vulnerable, 0: safe)
            - cwe / cwe_id: str (e.g. 'CWE-79', 'CWE-89')
            - language: str ('c', 'cpp', 'python', 'java')
            - task_type: str ('vulnerability_detection', 'insecure_coding', 'patch_generation')
            - test_cases / poc: list/dict (dynamic test execution metadata)
        """
        samples: List[CodeSample] = []
        for record in records:
            # Filter specifically for code samples suitable for vulnerability detection
            task_type = record.get("task_type", "vulnerability_detection")
            raw_id = str(record.get("task_id", record.get("id", "")))
            code_snippet = record.get("code", record.get("prompt_code", record.get("func", ""))).strip()
            if not code_snippet:
                continue

            target_val = record.get("is_vulnerable", record.get("label", record.get("target")))
            if target_val is not None:
                label = 1 if int(target_val) == 1 else 0
            else:
                label = None

            lang = record.get("language", "c").lower().strip()
            cwe = record.get("cwe", record.get("cwe_id"))
            cwe_str = str(cwe).strip() if cwe and str(cwe).lower() not in ("none", "null", "nan") else None

            sample = CodeSample(
                sample_id=f"secodeplt_{raw_id}",
                source_dataset="secodeplt",
                code=code_snippet,
                label=label,
                language=lang,
                provenance=ProvenanceType.SYNTHETIC.value,
                repository_id=record.get("seed_repo", "secodeplt_seed"),
                cwe_id=cwe_str,
                label_confidence=1.0 if label is not None else None,
                split=split,
                metadata={
                    "original_id": raw_id,
                    "task_type": task_type,
                    "mutation_technique": record.get("mutation_technique"),
                    "has_poc": bool(record.get("poc")),
                },
            )
            samples.append(sample)
        return samples

    def load(self) -> List[CodeSample]:
        """Load all SECODEPLT samples."""
        raw_file = self.raw_dir / "secodeplt.jsonl"
        if not raw_file.exists():
            return []

        records = []
        with open(raw_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return self.load_from_raw_records(records, split=DatasetSplit.SUPPLEMENTARY.value)

    def get_splits(self) -> Dict[str, List[CodeSample]]:
        """Return partitions.

        SECODEPLT is cataloged under 'supplementary' due to task format heterogeneity.
        """
        all_samples = self.load()
        return {DatasetSplit.SUPPLEMENTARY.value: all_samples}
