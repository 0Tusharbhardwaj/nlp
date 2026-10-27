"""Unit tests for Phase 2 dataset loaders, unified schemas, and data analyzers.

Compatible with both unittest and pytest.
"""

from pathlib import Path
import unittest

from src.data import (
    CodeSample,
    DatasetAnalyzer,
    DevignDatasetLoader,
    HumanVsAICodeDatasetLoader,
    LLMVulDatasetLoader,
    ProvenanceType,
    SeCodePLTDatasetLoader,
    detect_cross_dataset_overlap,
)
from src.utils.config import get_project_root


class TestDataLoadersAndAnalysis(unittest.TestCase):
    """Test suite verifying dataset ingestion, schema harmonization, and analysis."""

    def setUp(self):
        self.root = get_project_root()

    def test_code_sample_validation(self):
        """Verify CodeSample schema constraints and conversion methods."""
        # Valid sample
        sample = CodeSample(
            sample_id="test_001",
            source_dataset="devign",
            code="int main() { return 0; }",
            label=1,
            language="C",
            provenance="human",
            repository_id="qemu",
            cwe_id="CWE-119",
            label_confidence=1.0,
            split="train",
        )
        self.assertEqual(sample.language, "c")
        self.assertEqual(sample.label, 1)

        # Test dictionary serialization and deserialization
        data_dict = sample.to_dict()
        reconstructed = CodeSample.from_dict(data_dict)
        self.assertEqual(reconstructed.sample_id, sample.sample_id)
        self.assertEqual(reconstructed.cwe_id, "CWE-119")

        # Test invalid label
        with self.assertRaises(ValueError):
            CodeSample(sample_id="test_bad", source_dataset="devign", code="void f() {}", label=2)

        # Test empty code
        with self.assertRaises(ValueError):
            CodeSample(sample_id="test_bad", source_dataset="devign", code="   ", label=0)

    def test_devign_loader(self):
        """Verify Devign loader loads official splits and maps to unified schema."""
        loader = DevignDatasetLoader()
        splits = loader.get_splits()
        
        self.assertIn("train", splits)
        self.assertIn("valid", splits)
        self.assertIn("test", splits)
        
        train_samples = splits["train"]
        self.assertGreater(len(train_samples), 0)
        first_sample = train_samples[0]
        
        self.assertEqual(first_sample.source_dataset, "devign")
        self.assertEqual(first_sample.language, "c")
        self.assertEqual(first_sample.provenance, ProvenanceType.HUMAN.value)
        self.assertIn(first_sample.label, [0, 1])

    def test_llmvul_loader(self):
        """Verify LLMVul loader processes AI metadata, CWE IDs, and external split."""
        loader = LLMVulDatasetLoader()
        samples = loader.load()
        self.assertGreater(len(samples), 0)

        vuln_samples = [s for s in samples if s.label == 1]
        self.assertGreater(len(vuln_samples), 0)
        
        first_vuln = vuln_samples[0]
        self.assertEqual(first_vuln.source_dataset, "llmvul")
        self.assertTrue(first_vuln.provenance.startswith(ProvenanceType.AI_ASSISTED.value))
        self.assertIsNotNone(first_vuln.cwe_id)
        self.assertEqual(first_vuln.split, "external")

    def test_secodeplt_loader(self):
        """Verify SECODEPLT loader parses task formats and supplementary partition."""
        loader = SeCodePLTDatasetLoader()
        samples = loader.load()
        self.assertGreater(len(samples), 0)

        for s in samples:
            self.assertEqual(s.source_dataset, "secodeplt")
            self.assertEqual(s.provenance, ProvenanceType.SYNTHETIC.value)
            self.assertEqual(s.split, "supplementary")

    def test_human_vs_ai_loader(self):
        """Verify HumanVsAICode unrolls paired human and AI implementations."""
        loader = HumanVsAICodeDatasetLoader()
        samples = loader.load()
        self.assertGreater(len(samples), 0)

        provenances = {s.provenance for s in samples}
        self.assertIn(ProvenanceType.HUMAN.value, provenances)
        self.assertTrue(any("chatgpt" in p for p in provenances))
        
        # Languages should reflect Python
        languages = {s.language for s in samples}
        self.assertIn("python", languages)

    def test_analyzer_missing_values_and_labels(self):
        """Verify missing-value and label distribution metrics calculations."""
        loader = DevignDatasetLoader()
        samples = loader.load()
        analyzer = DatasetAnalyzer(samples, dataset_name="devign_test")

        missing = analyzer.analyze_missing_values()
        self.assertIn("code", missing)
        self.assertEqual(missing["code"]["missing_count"], 0)

        labels = analyzer.analyze_label_distribution()
        self.assertEqual(labels["total_samples"], len(samples))
        self.assertIn("vulnerability_rate", labels)
        self.assertIn("class_imbalance_ratio_0_to_1", labels)

    def test_exact_and_near_duplicates(self):
        """Verify exact and near duplicate detection algorithms."""
        dup_samples = [
            CodeSample(sample_id="s1", source_dataset="test", code="int add(int a, int b) { return a + b; }", label=0),
            CodeSample(sample_id="s2", source_dataset="test", code="int add(int a, int b) { return a + b; }", label=0),
            CodeSample(sample_id="s3", source_dataset="test", code="int add(int x, int y) { return x + y; }", label=0),
            CodeSample(sample_id="s4", source_dataset="test", code="void completely_different_function() { exit(1); }", label=1),
        ]
        analyzer = DatasetAnalyzer(dup_samples, dataset_name="dup_test")
        exact = analyzer.detect_exact_duplicates()
        
        self.assertEqual(exact["total_samples"], 4)
        self.assertEqual(exact["unique_code_count"], 3)
        self.assertEqual(exact["duplicate_sample_count"], 1)

        near = analyzer.detect_near_duplicates(threshold=0.80)
        self.assertGreater(near["near_duplicate_pairs_count"], 0)

    def test_cross_dataset_overlap(self):
        """Verify cross-dataset overlap and leakage detection."""
        set_a = [
            CodeSample(sample_id="a1", source_dataset="ds_a", code="void process() { int x = 10; }", label=0),
            CodeSample(sample_id="a2", source_dataset="ds_a", code="void clean() { free(ptr); }", label=1),
        ]
        set_b = [
            CodeSample(sample_id="b1", source_dataset="ds_b", code="void process() { int x = 10; }", label=0),
            CodeSample(sample_id="b2", source_dataset="ds_b", code="void unique_b() { return; }", label=0),
        ]

        overlap = detect_cross_dataset_overlap(set_a, set_b, name_a="SetA", name_b="SetB")
        self.assertEqual(overlap["exact_matches_count"], 1)
        self.assertEqual(overlap["exact_matches"][0]["SetA_sample_ids"], ["a1"])
        self.assertEqual(overlap["exact_matches"][0]["SetB_sample_id"], "b1")


if __name__ == "__main__":
    unittest.main()
