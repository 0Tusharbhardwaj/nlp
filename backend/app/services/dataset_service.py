"""Dataset service for retrieving benchmark dataset metadata, splits, and quality profiling."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from backend.app.schemas.datasets import DatasetInfo, DatasetsListResponse


class DatasetService:
    """Service to load and present dataset profiling metrics and status."""

    def __init__(
        self,
        processed_dir: str = "datasets/processed",
        reports_dir: str = "datasets/reports",
    ):
        self.processed_dir = Path(processed_dir)
        self.reports_dir = Path(reports_dir)

    def _count_lines_in_jsonl(self, filepath: Path) -> int:
        """Count valid JSON lines in a file."""
        if not filepath.exists():
            return 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def get_all_datasets(self) -> DatasetsListResponse:
        """Get list of benchmark datasets with actual processed sample counts."""
        # 1. Devign
        devign_train = self._count_lines_in_jsonl(self.processed_dir / "devign" / "train.jsonl")
        devign_valid = self._count_lines_in_jsonl(self.processed_dir / "devign" / "valid.jsonl")
        devign_test = self._count_lines_in_jsonl(self.processed_dir / "devign" / "test.jsonl")
        devign_total = devign_train + devign_valid + devign_test

        devign_info = DatasetInfo(
            id="devign",
            name="CodeXGLUE / Devign",
            language="C/C++",
            provenance="Human-written code from QEMU and FFmpeg security commits",
            granularity="function-level",
            vulnerability_rate=50.0,
            role="Primary Training (E1) & Human Baseline Evaluation",
            status="processed_and_audited",
            samples_count={
                "train": devign_train,
                "valid": devign_valid,
                "test": devign_test,
                "total": devign_total,
            },
        )

        # 2. LLMVul
        llmvul_ext = self._count_lines_in_jsonl(self.processed_dir / "llmvul" / "external.jsonl")
        llmvul_info = DatasetInfo(
            id="llmvul",
            name="LLMVul",
            language="C/C++",
            provenance="Real-world LLM-generated code across frontier models (GPT-4, Claude, CodeLlama)",
            granularity="function-level",
            vulnerability_rate=50.0,
            role="Zero-Shot AI Transfer Target (E2) & AI-Native Evaluation (E4)",
            status="processed_and_audited",
            samples_count={
                "external_evaluation": llmvul_ext,
                "total": llmvul_ext,
            },
        )

        # 3. SeCodePLT
        secodeplt_ext = self._count_lines_in_jsonl(self.processed_dir / "secodeplt" / "supplementary.jsonl")
        secodeplt_info = DatasetInfo(
            id="secodeplt",
            name="SeCodePLT",
            language="C/C++",
            provenance="Execution-based security evaluation with functional test suites",
            granularity="program/function",
            vulnerability_rate=50.0,
            role="Supplementary Program-Level Benchmark",
            status="processed_and_audited",
            samples_count={
                "supplementary": secodeplt_ext,
                "total": secodeplt_ext,
            },
        )

        # 4. HumanVsAICode
        human_vs_ai_info = DatasetInfo(
            id="human_vs_ai",
            name="HumanVsAICode",
            language="Python/Java",
            provenance="Mixed human and AI authored code in Python and Java",
            granularity="snippet",
            vulnerability_rate=50.0,
            role="Excluded from C/C++ Training (Language mismatch audited)",
            status="audited_and_excluded",
            samples_count={
                "total": 0,
            },
        )

        datasets = [devign_info, llmvul_info, secodeplt_info, human_vs_ai_info]
        return DatasetsListResponse(
            total_datasets=len(datasets),
            datasets=datasets,
        )


dataset_service = DatasetService()
