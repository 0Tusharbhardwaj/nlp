"""HumanVsAICode comparative dataset loader.

Reference:
- Hugging Face: OSS-forge/HumanVsAICode
- GitHub: dessertlab/Human_vs_AI_Code_Quality
- "Human-Written vs. AI-Generated Code: A Large-Scale Study of Defects,
  Vulnerabilities, and Complexity", ISSRE.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.base_loader import BaseDatasetLoader
from src.data.schema import CodeSample, DatasetSplit, ProvenanceType


class HumanVsAICodeDatasetLoader(BaseDatasetLoader):
    """Loader for the paired HumanVsAICode dataset across Python and Java implementations."""

    def __init__(self, raw_dir: Optional[Path] = None, processed_dir: Optional[Path] = None):
        super().__init__("human_vs_ai", raw_dir, processed_dir)

    def load_from_raw_records(self, records: List[Dict[str, Any]], split: str = DatasetSplit.SUPPLEMENTARY.value) -> List[CodeSample]:
        """Convert paired HumanVsAICode records into discrete CodeSample instances.
        
        Raw Schema:
            - pair_id / id: str
            - docstring / prompt: str
            - language: str ('python' or 'java')
            - human_code: str
            - chatgpt_code: Optional[str]
            - deepseek_code: Optional[str]
            - qwen_code: Optional[str]
            - defect_label / has_vulnerability: Optional[int/bool]
            - cwe_id: Optional[str]
        """
        samples: List[CodeSample] = []
        for record in records:
            pair_id = str(record.get("pair_id", record.get("id", "")))
            language = record.get("language", "python").lower().strip()
            cwe = record.get("cwe_id", record.get("cwe"))
            cwe_str = str(cwe).strip() if cwe and str(cwe).lower() not in ("none", "null", "nan") else None

            # 1. Unroll Human implementation
            human_code = record.get("human_code", "").strip()
            if human_code:
                human_sample = CodeSample(
                    sample_id=f"human_vs_ai_{pair_id}_human",
                    source_dataset="human_vs_ai",
                    code=human_code,
                    label=int(record["human_label"]) if "human_label" in record else None,
                    language=language,
                    provenance=ProvenanceType.HUMAN.value,
                    repository_id=record.get("repo_name", "codesearchnet_repo"),
                    cwe_id=cwe_str,
                    label_confidence=1.0 if "human_label" in record else None,
                    split=split,
                    metadata={"pair_id": pair_id, "docstring": record.get("docstring"), "variant": "human"},
                )
                samples.append(human_sample)

            # 2. Unroll AI implementations
            ai_variants = {
                "chatgpt": record.get("chatgpt_code"),
                "deepseek": record.get("deepseek_code"),
                "qwen": record.get("qwen_code"),
            }

            for model_name, ai_code in ai_variants.items():
                if ai_code and str(ai_code).strip():
                    ai_label_key = f"{model_name}_label"
                    ai_label = int(record[ai_label_key]) if ai_label_key in record else None

                    ai_sample = CodeSample(
                        sample_id=f"human_vs_ai_{pair_id}_{model_name}",
                        source_dataset="human_vs_ai",
                        code=str(ai_code).strip(),
                        label=ai_label,
                        language=language,
                        provenance=f"{ProvenanceType.AI_GENERATED.value}:{model_name}",
                        repository_id="llm_generation",
                        cwe_id=cwe_str,
                        label_confidence=1.0 if ai_label is not None else None,
                        split=split,
                        metadata={"pair_id": pair_id, "docstring": record.get("docstring"), "variant": model_name},
                    )
                    samples.append(ai_sample)

        return samples

    def load(self) -> List[CodeSample]:
        """Load all HumanVsAICode samples."""
        raw_file = self.raw_dir / "human_vs_ai.jsonl"
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
        """Return partitions under 'supplementary'."""
        all_samples = self.load()
        return {DatasetSplit.SUPPLEMENTARY.value: all_samples}
