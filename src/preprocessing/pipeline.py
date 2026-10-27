"""Unified reproducible preprocessing pipeline for SecureCode AI.

Coordinates:
- Source code preservation
- Classical baseline cleaning path (safe state-machine comment stripper)
- CodeBERT preservation path (syntax & structure intact)
- Untruncated token length distribution analysis
- Cross-split deduplication and leakage auditing
- Saving processed artifacts into datasets/processed/
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.base_loader import BaseDatasetLoader
from src.data.schema import CodeSample
from src.preprocessing.deduplicator import CrossSplitDeduplicator
from src.preprocessing.safe_cleaner import (
    prepare_for_classical_baseline,
    prepare_for_codebert,
)
from src.preprocessing.tokenizer_utils import (
    analyze_token_length_distribution,
    compute_untruncated_token_lengths,
    get_codebert_tokenizer,
)
from src.utils.config import get_project_root


class PreprocessingPipeline:
    """Manages preprocessing workflows for vulnerability benchmarks."""

    def __init__(
        self,
        dataset_name: str,
        config: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
    ):
        self.dataset_name = dataset_name
        self.config = config or {}
        self.project_root = get_project_root()
        self.output_dir = output_dir or (self.project_root / "datasets" / "processed" / dataset_name)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tokenizer = get_codebert_tokenizer(self.config.get("tokenizer_name", "microsoft/codebert-base"))

    def process_samples(self, samples: List[CodeSample]) -> List[Dict[str, Any]]:
        """Process a list of CodeSample objects, generating classical and transformer views.
        
        Guarantees:
        - raw_code is preserved intact.
        - classical_code has safe comment handling and whitespace normalization.
        - codebert_code retains complete syntax, identifiers, and brackets.
        - untruncated_token_length is measured BEFORE any truncation.
        - labels and provenance are strictly preserved.
        """
        strip_comments = self.config.get("classical_baseline", {}).get("strip_comments", False)
        codes = [s.code for s in samples]
        untruncated_lengths = compute_untruncated_token_lengths(codes, tokenizer=self.tokenizer)

        processed_records: List[Dict[str, Any]] = []
        for s, token_len in zip(samples, untruncated_lengths):
            record = {
                "sample_id": s.sample_id,
                "source_dataset": s.source_dataset,
                "raw_code": s.code,  # Complete raw source code preserved
                "classical_code": prepare_for_classical_baseline(s.code, strip_comments=strip_comments),
                "codebert_code": prepare_for_codebert(s.code),
                "label": s.label,
                "language": s.language,
                "provenance": s.provenance,
                "repository_id": s.repository_id,
                "cwe_id": s.cwe_id,
                "label_confidence": s.label_confidence,
                "split": s.split,
                "untruncated_token_length": token_len,
                "exceeds_512_tokens": bool(token_len > 512),
                "metadata": s.metadata,
            }
            processed_records.append(record)

        return processed_records

    def process_and_save_splits(
        self,
        splits: Dict[str, List[CodeSample]],
    ) -> Dict[str, Any]:
        """Process all splits, run leakage audit, analyze token lengths, and save artifacts."""
        processed_splits: Dict[str, List[Dict[str, Any]]] = {}
        all_token_lengths: List[int] = []

        # 1. Process each split
        for split_name, samples in splits.items():
            records = self.process_samples(samples)
            processed_splits[split_name] = records
            all_token_lengths.extend([r["untruncated_token_length"] for r in records])

            # Save split to JSONL
            split_file = self.output_dir / f"{split_name}.jsonl"
            with open(split_file, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

        # 2. Token length distribution analysis on untruncated lengths
        token_stats = analyze_token_length_distribution(all_token_lengths, thresholds=[128, 256, 512, 1024])

        # 3. Cross-split leakage and deduplication audit
        deduplicator = CrossSplitDeduplicator(splits)
        exact_leakage = deduplicator.audit_exact_cross_split_leakage()
        repo_overlap = deduplicator.audit_repository_overlap()

        report = {
            "dataset_name": self.dataset_name,
            "processed_splits_summary": {k: len(v) for k, v in processed_splits.items()},
            "token_length_distribution": token_stats,
            "cross_split_leakage_audit": exact_leakage,
            "repository_overlap_audit": repo_overlap,
        }

        # Save summary report
        report_file = self.output_dir / "preprocessing_summary.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report
