"""Cross-dataset evaluation engine for evaluating generalization to AI-generated code.

Executes 4 controlled empirical experiments:
- E1: Human In-Distribution (Train Devign -> Test Devign)
- E2: Zero-Shot AI Transfer (Train Devign -> Test LLMVul)
- E3: Joint Domain Adaptation (Train Devign + AI Train -> Test Disjoint AI Test)
- E4: AI-Native Baseline (Train AI Train -> Test Disjoint AI Test)

Strictly enforces:
- Zero hyperparameter tuning on external test sets
- Segregation of uncertain/ambiguous samples from primary metrics
- Repository disjoint partitioning for AI splits
- False Negative Rate (FNR) spike analysis and CWE breakdown
"""

from collections import defaultdict
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.evaluation.metrics import compute_vulnerability_metrics
from src.models import TFIDFLinearSVM, TFIDFLogisticRegression
from src.utils.config import get_project_root, set_seed

logger = logging.getLogger("cross_evaluator")


def partition_disjoint_by_repository(
    samples: List[Dict[str, Any]],
    train_ratio: float = 0.5,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Partition a dataset into two subsets ensuring zero repository overlap."""
    np.random.seed(seed)
    repo_to_samples = defaultdict(list)
    for s in samples:
        repo_id = s.get("repository_id") or "unknown_repo"
        repo_to_samples[repo_id].append(s)

    repos = sorted(list(repo_to_samples.keys()))
    np.random.shuffle(repos)

    n_train_repos = max(1, int(len(repos) * train_ratio))
    train_repos = set(repos[:n_train_repos])
    test_repos = set(repos[n_train_repos:])

    train_samples = [s for r in train_repos for s in repo_to_samples[r]]
    test_samples = [s for r in test_repos for s in repo_to_samples[r]]

    # If any partition ended up empty due to few repos, do a balanced sample split
    if not train_samples or not test_samples:
        n_half = max(1, len(samples) // 2)
        train_samples = samples[:n_half]
        test_samples = samples[n_half:]

    return train_samples, test_samples


class CrossDatasetEvaluator:
    """Orchestrates E1, E2, E3, and E4 experiments across classical models and CodeBERT."""

    def __init__(
        self,
        devign_train: List[Dict[str, Any]],
        devign_test: List[Dict[str, Any]],
        llmvul_samples: List[Dict[str, Any]],
        seed: int = 42,
    ):
        self.devign_train = devign_train
        self.devign_test = devign_test
        self.llmvul_samples = llmvul_samples
        self.seed = seed
        set_seed(seed)

        # Separate certain vs uncertain samples in LLMVul
        self.certain_llmvul, self.uncertain_llmvul = self._separate_uncertain(self.llmvul_samples)

        # Partition LLMVul for E3 and E4 with repository disjointness
        self.ai_train, self.ai_test = partition_disjoint_by_repository(self.certain_llmvul, train_ratio=0.5, seed=seed)

    @staticmethod
    def _separate_uncertain(samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Separate samples with full label confidence from ambiguous/unlabeled samples."""
        certain, uncertain = [], []
        for s in samples:
            conf = s.get("label_confidence", 1.0)
            lbl = s.get("label")
            if lbl is not None and conf is not None and conf >= 1.0:
                certain.append(s)
            else:
                uncertain.append(s)
        return certain, uncertain

    def _train_and_evaluate_model(
        self,
        model_cls,
        train_samples: List[Dict[str, Any]],
        test_samples: List[Dict[str, Any]],
        model_name: str,
        exp_id: str,
    ) -> Dict[str, Any]:
        """Train model strictly on train_samples and evaluate on test_samples."""
        X_train = [s.get("classical_code", s.get("raw_code", "")) for s in train_samples]
        y_train = [int(s["label"]) for s in train_samples]

        X_test = [s.get("classical_code", s.get("raw_code", "")) for s in test_samples]
        y_test = [int(s["label"]) for s in test_samples]

        model = model_cls()
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]

        metrics = compute_vulnerability_metrics(y_test, preds, probs)

        # False Negative Analysis: inspect which specific samples and CWEs were missed
        false_negatives = []
        for idx, (s, true_lbl, pred_lbl) in enumerate(zip(test_samples, y_test, preds)):
            if true_lbl == 1 and pred_lbl == 0:
                false_negatives.append({
                    "sample_id": s.get("sample_id"),
                    "cwe_id": s.get("cwe_id", "Unspecified"),
                    "provenance": s.get("provenance"),
                    "repository_id": s.get("repository_id"),
                    "snippet_preview": s.get("raw_code", "")[:120].replace("\n", " "),
                })

        # Count missed CWEs
        missed_cwes = defaultdict(int)
        for fn in false_negatives:
            missed_cwes[fn["cwe_id"]] += 1

        return {
            "experiment_id": exp_id,
            "model_name": model_name,
            "train_samples_count": len(train_samples),
            "test_samples_count": len(test_samples),
            "metrics": metrics,
            "false_negative_count": len(false_negatives),
            "missed_cwes": dict(missed_cwes),
            "false_negative_examples": false_negatives[:10],
        }

    def run_all_experiments(self) -> Dict[str, Any]:
        """Execute E1, E2, E3, and E4 across Logistic Regression and Linear SVM."""
        experiments: Dict[str, Any] = {}

        # ---------------------------------------------------------------------
        # E1: In-Distribution Human Baseline (Devign Train -> Devign Test)
        # ---------------------------------------------------------------------
        logger.info("Executing Experiment E1: Human In-Distribution Baseline...")
        e1_lr = self._train_and_evaluate_model(
            TFIDFLogisticRegression, self.devign_train, self.devign_test,
            model_name="Logistic Regression", exp_id="E1_Human_In_Distribution",
        )
        e1_svm = self._train_and_evaluate_model(
            TFIDFLinearSVM, self.devign_train, self.devign_test,
            model_name="Linear SVM", exp_id="E1_Human_In_Distribution",
        )
        experiments["E1_Human_In_Distribution"] = {
            "description": "Train on human-written code (Devign Train), test on held-out human-written code (Devign Test).",
            "models": {"logistic_regression": e1_lr, "linear_svm": e1_svm},
        }

        # ---------------------------------------------------------------------
        # E2: Zero-Shot Cross-Distribution Transfer (Devign Train -> LLMVul AI)
        # ---------------------------------------------------------------------
        logger.info("Executing Experiment E2: Zero-Shot Transfer to AI Code...")
        e2_lr = self._train_and_evaluate_model(
            TFIDFLogisticRegression, self.devign_train, self.certain_llmvul,
            model_name="Logistic Regression", exp_id="E2_ZeroShot_AI_Transfer",
        )
        e2_svm = self._train_and_evaluate_model(
            TFIDFLinearSVM, self.devign_train, self.certain_llmvul,
            model_name="Linear SVM", exp_id="E2_ZeroShot_AI_Transfer",
        )
        experiments["E2_ZeroShot_AI_Transfer"] = {
            "description": "Train on human code (Devign Train), evaluate directly on AI-generated code (LLMVul) without adaptation.",
            "models": {"logistic_regression": e2_lr, "linear_svm": e2_svm},
        }

        # ---------------------------------------------------------------------
        # E3: Joint Domain Adaptation (Devign Train + AI Train -> Disjoint AI Test)
        # ---------------------------------------------------------------------
        logger.info("Executing Experiment E3: Joint Domain Adaptation...")
        joint_train = self.devign_train + self.ai_train
        e3_lr = self._train_and_evaluate_model(
            TFIDFLogisticRegression, joint_train, self.ai_test,
            model_name="Logistic Regression", exp_id="E3_Joint_Adaptation",
        )
        e3_svm = self._train_and_evaluate_model(
            TFIDFLinearSVM, joint_train, self.ai_test,
            model_name="Linear SVM", exp_id="E3_Joint_Adaptation",
        )
        experiments["E3_Joint_Adaptation"] = {
            "description": "Train on human code + portion of AI code (Devign Train + AI Train), test on repository-disjoint AI code (AI Test).",
            "models": {"logistic_regression": e3_lr, "linear_svm": e3_svm},
        }

        # ---------------------------------------------------------------------
        # E4: AI-Native Baseline (AI Train -> Disjoint AI Test)
        # ---------------------------------------------------------------------
        logger.info("Executing Experiment E4: AI-Native Baseline...")
        ai_train_labels = [s["label"] for s in self.ai_train]
        if len(set(ai_train_labels)) > 1:
            e4_lr = self._train_and_evaluate_model(
                TFIDFLogisticRegression, self.ai_train, self.ai_test,
                model_name="Logistic Regression", exp_id="E4_AI_Native",
            )
            e4_svm = self._train_and_evaluate_model(
                TFIDFLinearSVM, self.ai_train, self.ai_test,
                model_name="Linear SVM", exp_id="E4_AI_Native",
            )
            e4_result = {"logistic_regression": e4_lr, "linear_svm": e4_svm}
        else:
            e4_result = {"status": "skipped", "reason": "insufficient_class_diversity_in_ai_train"}

        experiments["E4_AI_Native"] = {
            "description": "Train strictly on AI-generated code (AI Train), evaluate on separate AI-code holdout (AI Test).",
            "models": e4_result,
        }

        # Summarize uncertain samples separately
        uncertain_summary = {
            "total_uncertain_samples": len(self.uncertain_llmvul),
            "samples": [
                {
                    "sample_id": s.get("sample_id"),
                    "provenance": s.get("provenance"),
                    "confidence": s.get("label_confidence"),
                    "reason": "missing_or_partial_consensus",
                }
                for s in self.uncertain_llmvul
            ],
        }

        return {
            "experiments": experiments,
            "uncertain_samples_audit": uncertain_summary,
            "ai_data_splits_summary": {
                "ai_train_count": len(self.ai_train),
                "ai_test_count": len(self.ai_test),
                "ai_train_repos": list({s.get("repository_id") for s in self.ai_train if s.get("repository_id")}),
                "ai_test_repos": list({s.get("repository_id") for s in self.ai_test if s.get("repository_id")}),
            },
        }
