"""Unit tests for Phase 4 classical machine learning baselines and evaluation metrics.

Compatible with both unittest and pytest.
"""

from pathlib import Path
import tempfile
import unittest
import numpy as np

from src.evaluation import compute_vulnerability_metrics
from src.models import TFIDFLinearSVM, TFIDFLogisticRegression
from src.training import train_and_evaluate_baselines
from src.utils.config import get_project_root


class TestBaselines(unittest.TestCase):
    """Test suite verifying metric calculations, baseline models, and training engine."""

    def test_compute_vulnerability_metrics(self):
        """Verify metric calculation formulas, including FNR = 1 - Recall."""
        # y_true: [0, 0, 1, 1]
        # y_pred: [0, 1, 0, 1]
        # TN=1, FP=1, FN=1, TP=1
        y_true = [0, 0, 1, 1]
        y_pred = [0, 1, 0, 1]
        y_scores = [0.1, 0.7, 0.4, 0.9]

        m = compute_vulnerability_metrics(y_true, y_pred, y_scores)
        self.assertEqual(m["accuracy"], 0.5)
        self.assertEqual(m["precision"], 0.5)
        self.assertEqual(m["recall"], 0.5)
        self.assertEqual(m["f1_score"], 0.5)
        self.assertEqual(m["false_negative_rate"], 0.5)
        self.assertEqual(m["false_positive_rate"], 0.5)
        self.assertEqual(m["confusion_matrix"]["tn"], 1)
        self.assertEqual(m["confusion_matrix"]["fp"], 1)
        self.assertEqual(m["confusion_matrix"]["fn"], 1)
        self.assertEqual(m["confusion_matrix"]["tp"], 1)
        # Mathematical identity: FNR == 1 - Recall
        self.assertAlmostEqual(m["false_negative_rate"], 1.0 - m["recall"], places=4)

    def test_tfidf_logistic_regression(self):
        """Verify Logistic Regression training, prediction, and probability outputs."""
        train_texts = [
            "char *p = malloc(10); strcpy(p, src);",  # vuln
            "strncpy(dest, src, max); dest[max-1] = 0;",  # safe
            "sprintf(buf, \"%s\", input);",  # vuln
            "snprintf(buf, sizeof(buf), \"%s\", input);",  # safe
        ]
        train_labels = [1, 0, 1, 0]

        model = TFIDFLogisticRegression()
        # Unfitted call should raise RuntimeError
        with self.assertRaises(RuntimeError):
            model.predict(["test"])

        model.fit(train_texts, train_labels)
        self.assertTrue(model.is_fitted)

        preds = model.predict(train_texts)
        self.assertEqual(len(preds), 4)

        probs = model.predict_proba(train_texts)
        self.assertEqual(probs.shape, (4, 2))
        # Probabilities must sum to 1.0
        np.testing.assert_allclose(probs.sum(axis=1), np.ones(4), atol=1e-5)

    def test_tfidf_linear_svm(self):
        """Verify Linear SVM training, predictions, and calibrated probabilities."""
        train_texts = [
            "char *p = malloc(10); strcpy(p, src);",
            "strncpy(dest, src, max); dest[max-1] = 0;",
            "sprintf(buf, \"%s\", input);",
            "snprintf(buf, sizeof(buf), \"%s\", input);",
        ]
        train_labels = [1, 0, 1, 0]

        model = TFIDFLinearSVM()
        model.fit(train_texts, train_labels)
        self.assertTrue(model.is_fitted)

        preds = model.predict(train_texts)
        self.assertEqual(len(preds), 4)

        scores = model.decision_function(train_texts)
        self.assertEqual(len(scores), 4)

        probs = model.predict_proba(train_texts)
        self.assertEqual(probs.shape, (4, 2))
        np.testing.assert_allclose(probs.sum(axis=1), np.ones(4), atol=1e-5)

    def test_model_save_and_load(self):
        """Verify model serialization and deserialization reproducibility."""
        train_texts = ["strcpy(a, b);", "snprintf(a, s, b);"]
        train_labels = [1, 0]

        model = TFIDFLogisticRegression()
        model.fit(train_texts, train_labels)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_model.joblib"
            model.save(save_path)
            self.assertTrue(save_path.exists())

            loaded_model = TFIDFLogisticRegression.load(save_path)
            self.assertTrue(loaded_model.is_fitted)

            orig_preds = model.predict(train_texts)
            loaded_preds = loaded_model.predict(train_texts)
            np.testing.assert_array_equal(orig_preds, loaded_preds)

    def test_no_test_leakage_in_vectorizer(self):
        """Verify test samples are only transformed, never fitted."""
        train_texts = ["int x = 10;", "strcpy(a, b);"]
        train_labels = [0, 1]
        test_texts = ["new_unseen_token_xyz = 99;"]

        model = TFIDFLogisticRegression()
        model.fit(train_texts, train_labels)
        vocab_size_before = len(model.vectorizer.vocabulary_)

        # Transform test
        _ = model.transform(test_texts)
        vocab_size_after = len(model.vectorizer.vocabulary_)

        # Vocabulary must NOT change when transforming test data
        self.assertEqual(vocab_size_before, vocab_size_after)
        self.assertNotIn("new_unseen_token_xyz", model.vectorizer.vocabulary_)


if __name__ == "__main__":
    unittest.main()
