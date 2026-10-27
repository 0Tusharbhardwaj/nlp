"""Unit tests for Phase 5 CodeBERT dataset formatting, class weights, and checkpointing.

Compatible with both unittest and pytest.
"""

from pathlib import Path
import tempfile
import unittest

try:
    import torch
except ImportError:
    torch = None

from src.models import CodeBERTClassifier
from src.training.train_codebert import (
    VulnerabilityDataset,
    compute_class_weights,
    load_codebert_split_data,
)
from src.utils.config import get_project_root


class TestCodeBERTTraining(unittest.TestCase):
    """Test suite verifying CodeBERT data pipelines, class weights, and checkpoint structures."""

    def test_load_codebert_split_data(self):
        """Verify loading preprocessed devign codebert split data."""
        root = get_project_root()
        train_path = root / "datasets" / "processed" / "devign" / "train.jsonl"
        if train_path.exists():
            codes, labels = load_codebert_split_data(train_path)
            self.assertGreater(len(codes), 0)
            self.assertEqual(len(codes), len(labels))
            self.assertTrue(all(isinstance(c, str) for c in codes))
            self.assertTrue(all(l in (0, 1) for l in labels))

    def test_codebert_classifier_wrapper_fallback(self):
        """Verify CodeBERTClassifier handles local missing weight/torch environments gracefully."""
        classifier = CodeBERTClassifier()
        # In a local environment without downloaded weights, is_available() should cleanly report False
        if torch is None:
            self.assertFalse(classifier.is_available())
            with self.assertRaises(RuntimeError):
                classifier.predict(["void test() {}"])

    @unittest.skipIf(torch is None, "PyTorch not installed in local environment")
    def test_vulnerability_dataset(self):
        """Verify PyTorch VulnerabilityDataset item retrieval and tensor casting."""
        mock_encodings = {
            "input_ids": [[101, 200, 102], [101, 300, 102]],
            "attention_mask": [[1, 1, 1], [1, 1, 1]],
        }
        mock_labels = [0, 1]

        ds = VulnerabilityDataset(mock_encodings, mock_labels)
        self.assertEqual(len(ds), 2)

        item0 = ds[0]
        self.assertIn("input_ids", item0)
        self.assertIn("attention_mask", item0)
        self.assertIn("labels", item0)
        self.assertTrue(isinstance(item0["input_ids"], torch.Tensor))
        self.assertEqual(item0["labels"].item(), 0)

        item1 = ds[1]
        self.assertEqual(item1["labels"].item(), 1)

    @unittest.skipIf(torch is None, "PyTorch not installed in local environment")
    def test_compute_class_weights(self):
        """Verify balanced class weight computation: w_c = N / (2 * N_c)."""
        device = torch.device("cpu")
        labels = [0, 0, 0, 1]
        weights = compute_class_weights(labels, device)

        self.assertEqual(len(weights), 2)
        self.assertAlmostEqual(weights[0].item(), 4.0 / 6.0, places=3)
        self.assertAlmostEqual(weights[1].item(), 4.0 / 2.0, places=3)

    @unittest.skipIf(torch is None, "PyTorch not installed in local environment")
    def test_checkpoint_save_and_structure(self):
        """Verify checkpoint recovery payload structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_file = Path(tmpdir) / "checkpoint_test.pt"

            dummy_state = {
                "epoch": 1,
                "model_state_dict": {},
                "optimizer_state_dict": {},
                "best_f1": 0.75,
                "training_history": [{"epoch": 1, "val_f1": 0.75}],
            }
            torch.save(dummy_state, ckpt_file)
            self.assertTrue(ckpt_file.exists())

            loaded = torch.load(ckpt_file, map_location="cpu")
            self.assertEqual(loaded["epoch"], 1)
            self.assertEqual(loaded["best_f1"], 0.75)
            self.assertEqual(len(loaded["training_history"]), 1)


if __name__ == "__main__":
    unittest.main()
