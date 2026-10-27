"""LLMVul vulnerability dataset loader.

Reference:
- Farhad & Dass, "LLMVul: A Vulnerability-Labeled Dataset of LLM-Generated C/C++ Functions
  from Real Production Repositories", arXiv:2609.10945 (2024).
- Zenodo: DOI 10.5281/zenodo.22668216
- GitHub: Wahed08/LLMVul-Dataset
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.base_loader import BaseDatasetLoader
from src.data.schema import CodeSample, DatasetSplit, ProvenanceType


class LLMVulDatasetLoader(BaseDatasetLoader):
    """Loader for the LLMVul dataset containing real-world AI-generated C/C++ functions."""

    def __init__(self, raw_dir: Optional[Path] = None, processed_dir: Optional[Path] = None):
        super().__init__("llmvul", raw_dir, processed_dir)

    def load_from_raw_records(self, records: List[Dict[str, Any]], split: str = DatasetSplit.EXTERNAL.value) -> List[CodeSample]:
        """Convert raw LLMVul dictionary records (up to 34 columns) to CodeSample instances.
        
        Key columns mapped:
            - function_id / id: str
            - function_code / code / func: str (C/C++ function)
            - ensemble_label / is_vulnerable / target: int (1 if ensemble confirms vulnerability, 0 otherwise)
            - cwe / cwe_id: str (CWE classification, e.g. 'CWE-119', 'CWE-476')
            - repo_name / repository: str
            - commit_hash: str
            - ai_tool / provenance: str ('copilot', 'chatgpt', 'ai_assisted')
            - confidence / tool_agreement: float
        """
        samples: List[CodeSample] = []
        for record in records:
            raw_id = str(record.get("function_id", record.get("id", "")))
            func_code = record.get("function_code", record.get("code", record.get("func", ""))).strip()
            if not func_code:
                continue

            # Determine vulnerability label
            label_val = record.get("ensemble_label", record.get("is_vulnerable", record.get("target")))
            if label_val is not None:
                label = 1 if int(label_val) == 1 else 0
            else:
                label = None

            # Provenance attribution
            ai_tool = record.get("ai_tool", record.get("provenance", "ai_assisted"))
            provenance = f"{ProvenanceType.AI_ASSISTED.value}:{ai_tool}" if ai_tool else ProvenanceType.AI_ASSISTED.value

            # CWE identifier
            cwe = record.get("cwe", record.get("cwe_id"))
            cwe_str = str(cwe).strip() if cwe and str(cwe).lower() not in ("none", "null", "nan") else None

            # Tool agreement confidence
            confidence = record.get("confidence", record.get("label_confidence", 1.0 if label is not None else None))

            sample = CodeSample(
                sample_id=f"llmvul_{raw_id}",
                source_dataset="llmvul",
                code=func_code,
                label=label,
                language="cpp" if ("std::" in func_code or "cout" in func_code or "class " in func_code) else "c",
                provenance=provenance,
                repository_id=record.get("repo_name", record.get("repository")),
                cwe_id=cwe_str,
                label_confidence=float(confidence) if confidence is not None else None,
                split=split,
                metadata={
                    "original_id": raw_id,
                    "commit_hash": record.get("commit_hash"),
                    "ai_tool": ai_tool,
                    "static_analysis_tools": record.get("static_analysis_tools", {}),
                },
            )
            samples.append(sample)
        return samples

    def load(self) -> List[CodeSample]:
        """Load all LLMVul samples."""
        raw_file = self.raw_dir / "llmvul.jsonl"
        if not raw_file.exists():
            return []

        records = []
        with open(raw_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return self.load_from_raw_records(records, split=DatasetSplit.EXTERNAL.value)

    def get_splits(self) -> Dict[str, List[CodeSample]]:
        """Return partitions.

        By default, LLMVul serves as external evaluation (E2). If partitioned for E3/E4,
        returns 'train' and 'test' subsets.
        """
        all_samples = self.load()
        return {DatasetSplit.EXTERNAL.value: all_samples}
