"""Unit tests for Phase 6 cross-dataset evaluation engine and repository partitioning.

Compatible with both unittest and pytest.
"""

from pathlib import Path
import unittest

from src.evaluation import CrossDatasetEvaluator, partition_disjoint_by_repository
from src.utils.config import get_project_root


class TestCrossDatasetEvaluation(unittest.TestCase):
    """Test suite verifying E1-E4 cross-dataset experimental harness."""

    def setUp(self):
        self.devign_train = [
            {"sample_id": "tr1", "classical_code": "void bad_copy() { strcpy(a, b); }", "label": 1, "repository_id": "qemu"},
            {"sample_id": "tr2", "classical_code": "void good_copy() { strncpy(a, b, 10); }", "label": 0, "repository_id": "qemu"},
            {"sample_id": "tr3", "classical_code": "int parse() { char *p = malloc(10); return 0; }", "label": 1, "repository_id": "ffmpeg"},
            {"sample_id": "tr4", "classical_code": "int safe_parse() { return 0; }", "label": 0, "repository_id": "ffmpeg"},
        ]
        self.devign_test = [
            {"sample_id": "te1", "classical_code": "void test_v() { sprintf(b, \"%s\", s); }", "label": 1, "repository_id": "qemu"},
            {"sample_id": "te2", "classical_code": "void test_s() { snprintf(b, 10, \"%s\", s); }", "label": 0, "repository_id": "ffmpeg"},
        ]
        self.llmvul_samples = [
            {
                "sample_id": "ai1",
                "classical_code": "char *ai_fn() { char *b = malloc(10); sprintf(b, \"%s\", s); return b; }",
                "label": 1,
                "repository_id": "ai_repo_alpha",
                "cwe_id": "CWE-120",
                "label_confidence": 1.0,
                "provenance": "ai_assisted:copilot",
            },
            {
                "sample_id": "ai2",
                "classical_code": "std::string ai_clean() { return \"safe\"; }",
                "label": 0,
                "repository_id": "ai_repo_beta",
                "cwe_id": None,
                "label_confidence": 1.0,
                "provenance": "ai_assisted:chatgpt",
            },
            {
                "sample_id": "ai3",
                "classical_code": "int recv_msg() { return recv(s, b, 10, 0); }",
                "label": 1,
                "repository_id": "ai_repo_alpha",
                "cwe_id": "CWE-170",
                "label_confidence": 0.5,  # Ambiguous sample
                "provenance": "ai_assisted:copilot",
            },
        ]

    def test_partition_disjoint_by_repository(self):
        """Verify zero repository overlap between partitioned AI train and AI test splits."""
        train_sub, test_sub = partition_disjoint_by_repository(self.llmvul_samples, train_ratio=0.5, seed=42)
        
        train_repos = {s["repository_id"] for s in train_sub if s.get("repository_id")}
        test_repos = {s["repository_id"] for s in test_sub if s.get("repository_id")}
        
        # Must have zero intersection
        overlap = train_repos.intersection(test_repos)
        self.assertEqual(len(overlap), 0, f"Repository leakage detected: {overlap}")

    def test_cross_dataset_evaluator_runs_e1_to_e4(self):
        """Verify full execution of E1, E2, E3, and E4 experiments."""
        evaluator = CrossDatasetEvaluator(
            devign_train=self.devign_train,
            devign_test=self.devign_test,
            llmvul_samples=self.llmvul_samples,
            seed=42,
        )

        results = evaluator.run_all_experiments()

        self.assertIn("experiments", results)
        self.assertIn("E1_Human_In_Distribution", results["experiments"])
        self.assertIn("E2_ZeroShot_AI_Transfer", results["experiments"])
        self.assertIn("E3_Joint_Adaptation", results["experiments"])
        self.assertIn("E4_AI_Native", results["experiments"])

        # Check that uncertain sample (ai3 with confidence=0.5) was quarantined
        uncertain_audit = results["uncertain_samples_audit"]
        self.assertEqual(uncertain_audit["total_uncertain_samples"], 1)
        self.assertEqual(uncertain_audit["samples"][0]["sample_id"], "ai3")

        # Verify metric keys are populated
        e1_lr_metrics = results["experiments"]["E1_Human_In_Distribution"]["models"]["logistic_regression"]["metrics"]
        self.assertIn("accuracy", e1_lr_metrics)
        self.assertIn("false_negative_rate", e1_lr_metrics)
        self.assertIn("f1_score", e1_lr_metrics)


if __name__ == "__main__":
    unittest.main()
