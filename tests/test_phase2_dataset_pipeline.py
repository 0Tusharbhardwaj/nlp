"""Unit and integration tests for Phase 2 full-scale dataset pipeline."""

import json
from pathlib import Path
import unittest

from src.data.llmvul_partitioner import LLMVulPartitioner
from src.data.secodeplt_adapter import SeCodePLTAdapter


class TestPhase2DatasetPipeline(unittest.TestCase):
    """Test suite verifying Phase 2 full-scale dataset modules and partition integrity."""

    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.processed_dir = cls.project_root / "datasets" / "processed"
        cls.reports_dir = cls.project_root / "datasets" / "reports"

    def test_download_manifest_exists(self):
        """Verify download manifest exists and contains records for all three datasets."""
        manifest_path = self.project_root / "datasets" / "download_manifest.json"
        self.assertTrue(manifest_path.exists(), "download_manifest.json must exist")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        self.assertIn("devign", manifest.get("datasets", {}))
        self.assertIn("llmvul", manifest.get("datasets", {}))
        self.assertIn("secodeplt", manifest.get("datasets", {}))

    def test_secodeplt_adapter(self):
        """Verify SeCodePLT adapter produces balanced, valid binary evaluation instances."""
        adapter = SeCodePLTAdapter()
        samples = adapter.adapt_samples()
        
        self.assertGreater(len(samples), 0, "SeCodePLT adapter must produce samples")
        self.assertEqual(len(samples), 2480, "Expected exactly 2,480 instances from 1,240 tasks")
        
        # Check label balance
        vuln_count = sum(1 for s in samples if s["target"] == 1)
        safe_count = sum(1 for s in samples if s["target"] == 0)
        self.assertEqual(vuln_count, safe_count, "SeCodePLT evaluation pairs must be strictly balanced (1:1)")
        
        # Verify placeholders were replaced
        for s in samples[:20]:
            self.assertNotIn("##SECCODEPLT##", s["code"])
            self.assertIn(s["target"], [0, 1])

    def test_llmvul_partitions_disjointness(self):
        """Verify strict repository disjointness between LLMVul train and test partitions."""
        meta_path = self.processed_dir / "llmvul_partitions_meta.json"
        self.assertTrue(meta_path.exists(), "llmvul_partitions_meta.json must exist")
        
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        train_repos = set(meta["train_repos"])
        test_repos = set(meta["test_repos"])
        
        # Critical scientific constraint: ZERO repository overlap
        overlap = train_repos & test_repos
        self.assertEqual(len(overlap), 0, f"FATAL: Repository overlap detected in LLMVul: {overlap}")
        
        # Verify sample counts match stats
        stats = meta["stats"]
        self.assertEqual(stats["total_raw_rows"], 21430)
        self.assertEqual(stats["certain_rows"], 18751)
        self.assertEqual(stats["uncertain_quarantined"], 2679)

    def test_all_reports_generated(self):
        """Verify all seven required Phase 2 reports are present in datasets/reports/."""
        expected_reports = [
            "FULL_DATASET_INVENTORY.md",
            "FULL_DATASET_STATISTICS.md",
            "LABEL_DISTRIBUTION_REPORT.md",
            "REPOSITORY_OVERLAP_REPORT.md",
            "EXACT_DUPLICATE_REPORT.md",
            "NEAR_DUPLICATE_REPORT.md",
            "TOKEN_LENGTH_DISTRIBUTION_REPORT.md",
            "DATASET_CHECKSUMS.sha256",
        ]
        for rep in expected_reports:
            p = self.reports_dir / rep
            self.assertTrue(p.exists(), f"Report missing: {rep}")
            self.assertGreater(p.stat().st_size, 100, f"Report {rep} appears truncated or empty")


if __name__ == "__main__":
    unittest.main()
