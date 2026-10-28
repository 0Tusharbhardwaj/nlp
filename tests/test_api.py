"""Unit and integration tests for SecureCode AI FastAPI backend endpoints."""

import unittest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.model_service import ModelManager



class TestAPIEndpoints(unittest.TestCase):
    """Test suite covering health, models, scanning, datasets, and experiment endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        """Verify root endpoint provides API metadata and documentation links."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "SecureCode AI Backend")
        self.assertIn("docs", data)
        self.assertEqual(data["api_v1"], "/api/v1")

    def test_health_endpoints(self):
        """Verify root health check and versioned diagnostics endpoint."""
        # Root health check
        root_resp = self.client.get("/health")
        self.assertEqual(root_resp.status_code, 200)
        self.assertEqual(root_resp.json()["status"], "healthy")

        # API v1 health check with diagnostics
        v1_resp = self.client.get("/api/v1/health")
        self.assertEqual(v1_resp.status_code, 200)
        data = v1_resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gpu_available", data)
        self.assertIn("models_ready_count", data)
        self.assertGreaterEqual(data["models_ready_count"], 2)

    def test_list_and_get_models(self):
        """Verify models listing and metadata retrieval for valid and invalid model IDs."""
        # List all models
        list_resp = self.client.get("/api/v1/models")
        self.assertEqual(list_resp.status_code, 200)
        data = list_resp.json()
        self.assertIn("models", data)
        self.assertEqual(data["default_model"], "tfidf_logistic_regression")
        model_ids = [m["id"] for m in data["models"]]
        self.assertIn("tfidf_logistic_regression", model_ids)
        self.assertIn("tfidf_linear_svm", model_ids)
        self.assertIn("codebert", model_ids)

        # Get specific model: tfidf_logistic_regression
        lr_resp = self.client.get("/api/v1/models/tfidf_logistic_regression")
        self.assertEqual(lr_resp.status_code, 200)
        lr_data = lr_resp.json()
        self.assertEqual(lr_data["id"], "tfidf_logistic_regression")
        self.assertEqual(lr_data["status"], "ready")

        # Unknown model returns 404
        unknown_resp = self.client.get("/api/v1/models/non_existent_model_id")
        self.assertEqual(unknown_resp.status_code, 404)

    def test_single_scan_logistic_regression(self):
        """Verify vulnerability scan using TF-IDF + Logistic Regression."""
        payload = {
            "code": "void buffer_overflow(char *str) { char buf[16]; strcpy(buf, str); }",
            "model_id": "tfidf_logistic_regression",
            "language": "c",
        }
        response = self.client.post("/api/v1/scan", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model_id"], "tfidf_logistic_regression")
        self.assertIn(data["prediction"], [0, 1])
        self.assertIsInstance(data["is_vulnerable"], bool)
        self.assertGreaterEqual(data["confidence"], 0.0)
        self.assertLessEqual(data["confidence"], 1.0)
        self.assertIn("safe", data["probabilities"])
        self.assertIn("vulnerable", data["probabilities"])
        prob_sum = data["probabilities"]["safe"] + data["probabilities"]["vulnerable"]
        self.assertAlmostEqual(prob_sum, 1.0, places=3)
        self.assertGreater(data["inference_time_ms"], 0.0)
        self.assertIn("disclaimer", data)

    def test_single_scan_linear_svm(self):
        """Verify vulnerability scan using TF-IDF + Linear SVM."""
        payload = {
            "code": "int safe_addition(int a, int b) { return a + b; }",
            "model_id": "tfidf_linear_svm",
            "language": "c",
        }
        response = self.client.post("/api/v1/scan", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model_id"], "tfidf_linear_svm")
        self.assertEqual(data["requested_model"], "tfidf_linear_svm")
        self.assertEqual(data["actual_model"], "tfidf_linear_svm")
        self.assertFalse(data["fallback_used"])
        self.assertIn(data["prediction"], [0, 1])
        self.assertIn("safe", data["probabilities"])
        self.assertIn("vulnerable", data["probabilities"])

    def test_codebert_execution_and_transparent_fallback(self):
        """Verify CodeBERT execution when available, and transparent attribution when fallback is allowed."""
        payload = {
            "code": "void test_func() { char b[10]; gets(b); }",
            "model_id": "codebert",
            "allow_fallback": False,
        }
        manager = ModelManager.get_instance()
        manager.initialize()

        if manager.loaded_models.get("codebert") is not None:
            # CodeBERT is loaded and available
            response = self.client.post("/api/v1/scan", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["actual_model"], "codebert")
            self.assertFalse(data["fallback_used"])

        # Simulate unavailable runtime to verify 503 and transparent fallback
        orig_cb = manager.loaded_models.get("codebert")
        try:
            manager.loaded_models["codebert"] = None
            response = self.client.post("/api/v1/scan", json=payload)
            self.assertEqual(response.status_code, 503)
            self.assertIn("unavailable", response.json()["detail"].lower())

            # When client explicitly permits fallback:
            payload["allow_fallback"] = True
            fb_response = self.client.post("/api/v1/scan", json=payload)
            self.assertEqual(fb_response.status_code, 200)
            fb_data = fb_response.json()
            self.assertEqual(fb_data["requested_model"], "codebert")
            self.assertTrue(fb_data["fallback_used"])
            self.assertIn("Fallback for CodeBERT", fb_data["model_name"])
        finally:
            if orig_cb is not None:
                manager.loaded_models["codebert"] = orig_cb


    def test_scan_validation_errors(self):
        """Verify proper validation errors on invalid inputs."""
        # 1. Empty string code snippet -> 422
        resp_empty = self.client.post("/api/v1/scan", json={"code": ""})
        self.assertEqual(resp_empty.status_code, 422)

        # 2. Whitespace-only code snippet -> 422
        resp_spaces = self.client.post("/api/v1/scan", json={"code": "   \n\t  "})
        self.assertEqual(resp_spaces.status_code, 422)

        # 3. Missing code parameter -> 422
        resp_missing = self.client.post("/api/v1/scan", json={})
        self.assertEqual(resp_missing.status_code, 422)

        # 4. Unknown model ID -> 400
        resp_bad_model = self.client.post(
            "/api/v1/scan",
            json={"code": "int x = 42;", "model_id": "imaginary_model"},
        )
        self.assertEqual(resp_bad_model.status_code, 400)

    def test_batch_scan(self):
        """Verify batch scanning of multiple code snippets."""
        payload = {
            "items": [
                {"id": "item-1", "code": "void bad() { gets(buf); }", "language": "c"},
                {"id": "item-2", "code": "int good(int x) { return x * 2; }", "language": "c"},
            ],
            "model_id": "tfidf_logistic_regression",
        }
        response = self.client.post("/api/v1/scan/batch", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_processed"], 2)
        self.assertEqual(len(data["results"]), 2)
        self.assertGreater(data["total_time_ms"], 0.0)

    def test_datasets_endpoint(self):
        """Verify datasets profiling endpoint returns evaluated benchmarks."""
        response = self.client.get("/api/v1/datasets")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_datasets"], 4)
        dataset_ids = [d["id"] for d in data["datasets"]]
        self.assertIn("devign", dataset_ids)
        self.assertIn("llmvul", dataset_ids)
        self.assertIn("secodeplt", dataset_ids)
        self.assertIn("human_vs_ai", dataset_ids)

    def test_experiments_endpoints(self):
        """Verify experiment metrics and cross-dataset comparative audit endpoints."""
        # Experiments list
        exp_resp = self.client.get("/api/v1/experiments")
        self.assertEqual(exp_resp.status_code, 200)
        data = exp_resp.json()
        self.assertIn("experiments", data)
        self.assertIn("scientific_disclaimer", data)
        exp_ids = [e["experiment_id"] for e in data["experiments"]]
        self.assertIn("E1_Human_In_Distribution", exp_ids)
        self.assertIn("E2_ZeroShot_AI_Transfer", exp_ids)

        # Comparison summary
        comp_resp = self.client.get("/api/v1/experiments/comparison")
        self.assertEqual(comp_resp.status_code, 200)
        comp_data = comp_resp.json()
        self.assertIn("thesis", comp_data)
        self.assertIn("experiments", comp_data)


if __name__ == "__main__":
    unittest.main()
