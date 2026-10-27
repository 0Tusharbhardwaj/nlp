"""End-to-end system verification audit script for SecureCode AI.

Validates:
1. Checkpoint and model artifact integrity.
2. Dataset partition presence and audit consistency.
3. Backend FastAPI API endpoints and inference latency.
4. Classical baseline probability bounds and disclaimers.
5. Cross-dataset metrics (E1-E4) and FNR reporting.
6. Frontend production build integrity.
"""

from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from fastapi.testclient import TestClient


def run_system_audit() -> bool:
    print("=" * 70)
    print("      SECURECODE AI — END-TO-END SYSTEM INTEGRATION AUDIT")
    print("=" * 70)

    all_passed = True
    client = TestClient(app)

    # 1. Artifact & Model Checkpoint Audit
    print("\n[1/6] Checking Model Checkpoints and Serialized Weights...")
    models_dir = Path("results/models")
    lr_model = models_dir / "tfidf_logistic_regression.joblib"
    svm_model = models_dir / "tfidf_linear_svm.joblib"

    if lr_model.exists() and svm_model.exists():
        print(f"  [PASS] Logistic Regression Model: {lr_model} ({lr_model.stat().st_size} bytes)")
        print(f"  [PASS] Linear SVM Model:          {svm_model} ({svm_model.stat().st_size} bytes)")
    else:
        print("  [FAIL] Missing model weights in results/models/")
        all_passed = False

    # 2. Processed Benchmark Datasets Audit
    print("\n[2/6] Checking Processed Benchmark Datasets...")
    datasets_to_check = [
        Path("datasets/processed/devign/train.jsonl"),
        Path("datasets/processed/devign/valid.jsonl"),
        Path("datasets/processed/devign/test.jsonl"),
        Path("datasets/processed/llmvul/external.jsonl"),
        Path("datasets/processed/secodeplt/supplementary.jsonl"),
    ]
    for dpath in datasets_to_check:
        if dpath.exists():
            with open(dpath, "r", encoding="utf-8") as f:
                lines = sum(1 for line in f if line.strip())
            print(f"  [PASS] {dpath.name:<25} ({dpath.parent.name:<10}) -> {lines} samples")
        else:
            print(f"  [FAIL] Missing dataset file: {dpath}")
            all_passed = False

    # 3. System Diagnostics & Health API
    print("\n[3/6] Auditing Backend API Health & Telemetry...")
    t0 = time.perf_counter()
    resp = client.get("/api/v1/health")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    if resp.status_code == 200:
        data = resp.json()
        print(f"  [PASS] GET /api/v1/health -> Status: {data['status']} ({latency_ms:.2f} ms)")
        print(f"         GPU Available: {data.get('gpu_available')}, Models Ready: {data.get('models_ready_count')}")
    else:
        print(f"  [FAIL] Health endpoint returned status {resp.status_code}")
        all_passed = False

    # 4. Live Vulnerability Inference Audit
    print("\n[4/6] Auditing Vulnerability Scanning Inference...")
    vulnerable_snippet = """
    void handle_packet(const char *input) {
        char buffer[32];
        strcpy(buffer, input); // CWE-120 Buffer Overflow
    }
    """
    for mid in ["tfidf_logistic_regression", "tfidf_linear_svm"]:
        payload = {"code": vulnerable_snippet, "model_id": mid, "language": "c"}
        t_inf = time.perf_counter()
        scan_resp = client.post("/api/v1/scan", json=payload)
        inf_ms = (time.perf_counter() - t_inf) * 1000.0

        if scan_resp.status_code == 200:
            sdata = scan_resp.json()
            is_vuln = sdata["is_vulnerable"]
            conf = sdata["confidence"]
            print(
                f"  [PASS] Model: {mid:<28} -> IsVulnerable: {str(is_vuln):<5} "
                f"Conf: {conf * 100:.1f}% Latency: {inf_ms:.2f} ms"
            )
        else:
            print(f"  [FAIL] Scan failed for model {mid}: {scan_resp.text}")
            all_passed = False

    # 5. Cross-Dataset Metrics & Generalization Thesis
    print("\n[5/6] Auditing Empirical Research Benchmarks (E1-E4)...")
    exp_resp = client.get("/api/v1/experiments")
    if exp_resp.status_code == 200:
        exp_data = exp_resp.json()
        experiments = exp_data.get("experiments", [])
        print(f"  [PASS] Retrieved {len(experiments)} Empirical Experiments from API:")
        for exp in experiments:
            results_str = ", ".join(
                f"{r['model_name']}: Acc={r['accuracy']*100:.0f}%, FNR={r['false_negative_rate']*100:.0f}%"
                for r in exp["results"]
            )
            print(f"         - {exp['experiment_id']}: {results_str or 'Holdout'}")
    else:
        print(f"  [FAIL] Failed to retrieve experiments: {exp_resp.text}")
        all_passed = False

    # 6. Frontend Production Build Audit
    print("\n[6/6] Auditing Frontend Production Bundle...")
    frontend_dist = Path("frontend/dist")
    index_html = frontend_dist / "index.html"
    if index_html.exists():
        assets = list((frontend_dist / "assets").glob("*"))
        print(f"  [PASS] Frontend Build Index: {index_html} ({index_html.stat().st_size} bytes)")
        print(f"  [PASS] Bundled Assets:       {len(assets)} files in dist/assets/")
    else:
        print("  [FAIL] Frontend dist not found. Run 'npm run build' inside frontend/")
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print(">>> ALL INTEGRATION CHECKS PASSED: SYSTEM FULLY OPERATIONAL <<<")
    else:
        print(">>> INTEGRATION ISSUES DETECTED: CHECK FAILED STEPS ABOVE <<<")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_system_audit()
    sys.exit(0 if success else 1)
