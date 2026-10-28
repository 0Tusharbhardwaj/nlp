"""Official Full-Scale Dataset Downloader for SecureCode AI.

Downloads and authenticates official releases for:
1. CodeXGLUE / Devign (Hugging Face / Microsoft Research)
2. LLMVul (Farhad & Dass / GitHub & Zenodo release)
3. SECODEPLT (UCSB-SURFI / Hugging Face release)

Preserves official splits, computes SHA256 hashes, and records a download manifest.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional
import urllib.request
import pyarrow.parquet as pq

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


DOWNLOAD_TARGETS = {
    "devign": {
        "train": {
            "url": "https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/train-00000-of-00001.parquet",
            "filename": "train.parquet",
            "jsonl_name": "train.jsonl",
            "split": "train",
        },
        "validation": {
            "url": "https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/validation-00000-of-00001.parquet",
            "filename": "validation.parquet",
            "jsonl_name": "valid.jsonl",
            "split": "valid",
        },
        "test": {
            "url": "https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data/test-00000-of-00001.parquet",
            "filename": "test.parquet",
            "jsonl_name": "test.jsonl",
            "split": "test",
        },
    },
    "llmvul": {
        "main_dataset": {
            "url": "https://raw.githubusercontent.com/Wahed08/LLMVul-Dataset/main/data/LLMVul_v3-Updated.csv",
            "filename": "LLMVul_v3-Updated.csv",
            "description": "Full production repository LLM-generated functions with static tool consensus",
        },
        "manual_validation": {
            "url": "https://raw.githubusercontent.com/Wahed08/LLMVul-Dataset/main/manual_validation_set/LLMVul_manual_review_100-Updated.csv",
            "filename": "LLMVul_manual_review_100-Updated.csv",
            "description": "Expert manually validated holdout partition",
        },
    },
    "secodeplt": {
        "c_vulnerability_detection": {
            "url": "https://huggingface.co/datasets/UCSB-SURFI/SeCodePLT/resolve/main/data/c_vulnerability_detection-00000-of-00001.parquet",
            "filename": "c_vulnerability_detection.parquet",
            "jsonl_name": "c_vulnerability_detection.jsonl",
            "description": "C function vulnerability detection tasks with paired vulnerable/patched code references",
        },
    },
}


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file_with_retry(url: str, dest_path: Path, max_retries: int = 3, timeout: int = 60) -> int:
    """Download file from URL with chunked streaming and retries."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    headers = {
        "User-Agent": "SecureCodeAI-Research-Downloader/2.0 (Academic Research; Python urllib)",
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  --> Downloading: {url} (Attempt {attempt}/{max_retries})")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                start_time = time.time()

                with open(temp_path, "wb") as out_file:
                    while chunk := response.read(65536):
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and downloaded % (1024 * 1024 * 2) < 65536:
                            percent = (downloaded / total_size) * 100
                            mb = downloaded / (1024 * 1024)
                            speed = mb / max(time.time() - start_time, 0.01)
                            print(f"\r      Progress: {mb:.1f} MB / {total_size / (1024 * 1024):.1f} MB ({percent:.1f}%) [{speed:.1f} MB/s]", end="", flush=True)

                print(f"\r      Downloaded: {downloaded / (1024 * 1024):.2f} MB complete.                      ")
                temp_path.replace(dest_path)
                return downloaded
        except Exception as e:
            print(f"  [!] Download attempt {attempt} failed: {e}")
            if temp_path.exists():
                temp_path.unlink()
            if attempt < max_retries:
                time.sleep(2 * attempt)
            else:
                raise e
    return 0


def convert_devign_parquet_to_jsonl(parquet_path: Path, jsonl_path: Path) -> int:
    """Convert CodeXGLUE/Devign parquet file into JSONL format preserving official schema."""
    table = pq.read_table(parquet_path)
    count = 0
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for i in range(table.num_rows):
            record = {
                "id": table.column("id")[i].as_py(),
                "func": table.column("func")[i].as_py(),
                "target": 1 if bool(table.column("target")[i].as_py()) else 0,
                "project": str(table.column("project")[i].as_py()),
                "commit_id": str(table.column("commit_id")[i].as_py()),
            }
            f.write(json.dumps(record) + "\n")
            count += 1
    return count


def convert_secodeplt_parquet_to_jsonl(parquet_path: Path, jsonl_path: Path) -> int:
    """Convert SeCodePLT parquet file to JSONL format."""
    table = pq.read_table(parquet_path)
    count = 0
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for i in range(table.num_rows):
            record = {col: table.column(col)[i].as_py() for col in table.column_names}
            f.write(json.dumps(record) + "\n")
            count += 1
    return count


def run_full_download(dest_root: Optional[Path] = None) -> Dict[str, Any]:
    """Execute download of all full-scale datasets and generate manifests."""
    if dest_root is None:
        dest_root = root_dir / "datasets" / "raw" / "full"

    manifest_path = root_dir / "datasets" / "download_manifest.json"
    checksum_path = root_dir / "datasets" / "reports" / "DATASET_CHECKSUMS.sha256"
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dest_root": str(dest_root),
        "datasets": {},
    }
    checksums: List[str] = []

    print("=================================================================")
    print(" SecureCode AI - Full-Scale Dataset Acquisition Pipeline         ")
    print("=================================================================")
    print(f"Target Directory: {dest_root}")

    # 1. Download CodeXGLUE / Devign
    print("\n--- 1. CodeXGLUE / Devign (Official Benchmark) ---")
    devign_dest = dest_root / "devign"
    manifest["datasets"]["devign"] = {"files": {}, "status": "pending"}

    for split_key, info in DOWNLOAD_TARGETS["devign"].items():
        pq_file = devign_dest / info["filename"]
        jsonl_file = devign_dest / info["jsonl_name"]

        if not pq_file.exists():
            download_file_with_retry(info["url"], pq_file)
        else:
            print(f"  [OK] Existing file detected: {pq_file.name}")

        sha = compute_sha256(pq_file)
        checksums.append(f"{sha}  {pq_file.relative_to(root_dir)}")

        # Convert to JSONL
        if not jsonl_file.exists():
            n_rows = convert_devign_parquet_to_jsonl(pq_file, jsonl_file)
            print(f"  [OK] Converted {pq_file.name} -> {jsonl_file.name} ({n_rows:,} records)")
        else:
            n_rows = sum(1 for _ in open(jsonl_file, "r", encoding="utf-8"))
            print(f"  [OK] JSONL partition ready: {jsonl_file.name} ({n_rows:,} records)")

        jsonl_sha = compute_sha256(jsonl_file)
        checksums.append(f"{jsonl_sha}  {jsonl_file.relative_to(root_dir)}")

        manifest["datasets"]["devign"]["files"][split_key] = {
            "parquet_file": str(pq_file.relative_to(root_dir)),
            "parquet_bytes": pq_file.stat().st_size,
            "parquet_sha256": sha,
            "jsonl_file": str(jsonl_file.relative_to(root_dir)),
            "jsonl_sha256": jsonl_sha,
            "sample_count": n_rows,
            "source_url": info["url"],
        }
    manifest["datasets"]["devign"]["status"] = "complete"

    # 2. Download LLMVul
    print("\n--- 2. LLMVul (Production LLM Benchmark) ---")
    llmvul_dest = dest_root / "llmvul"
    manifest["datasets"]["llmvul"] = {"files": {}, "status": "pending"}

    for file_key, info in DOWNLOAD_TARGETS["llmvul"].items():
        csv_file = llmvul_dest / info["filename"]
        if not csv_file.exists():
            download_file_with_retry(info["url"], csv_file)
        else:
            print(f"  [OK] Existing file detected: {csv_file.name}")

        sha = compute_sha256(csv_file)
        checksums.append(f"{sha}  {csv_file.relative_to(root_dir)}")

        manifest["datasets"]["llmvul"]["files"][file_key] = {
            "csv_file": str(csv_file.relative_to(root_dir)),
            "csv_bytes": csv_file.stat().st_size,
            "csv_sha256": sha,
            "description": info["description"],
            "source_url": info["url"],
        }
    manifest["datasets"]["llmvul"]["status"] = "complete"

    # 3. Download SECODEPLT (c_vulnerability_detection)
    print("\n--- 3. SECODEPLT (Supplementary C Benchmark) ---")
    secodeplt_dest = dest_root / "secodeplt"
    manifest["datasets"]["secodeplt"] = {"files": {}, "status": "pending"}

    for task_key, info in DOWNLOAD_TARGETS["secodeplt"].items():
        pq_file = secodeplt_dest / info["filename"]
        jsonl_file = secodeplt_dest / info["jsonl_name"]

        if not pq_file.exists():
            download_file_with_retry(info["url"], pq_file)
        else:
            print(f"  [OK] Existing file detected: {pq_file.name}")

        sha = compute_sha256(pq_file)
        checksums.append(f"{sha}  {pq_file.relative_to(root_dir)}")

        if not jsonl_file.exists():
            n_rows = convert_secodeplt_parquet_to_jsonl(pq_file, jsonl_file)
            print(f"  [OK] Converted {pq_file.name} -> {jsonl_file.name} ({n_rows:,} records)")
        else:
            n_rows = sum(1 for _ in open(jsonl_file, "r", encoding="utf-8"))
            print(f"  [OK] JSONL ready: {jsonl_file.name} ({n_rows:,} records)")

        jsonl_sha = compute_sha256(jsonl_file)
        checksums.append(f"{jsonl_sha}  {jsonl_file.relative_to(root_dir)}")

        manifest["datasets"]["secodeplt"]["files"][task_key] = {
            "parquet_file": str(pq_file.relative_to(root_dir)),
            "parquet_bytes": pq_file.stat().st_size,
            "parquet_sha256": sha,
            "jsonl_file": str(jsonl_file.relative_to(root_dir)),
            "jsonl_sha256": jsonl_sha,
            "sample_count": n_rows,
            "description": info["description"],
            "source_url": info["url"],
        }
    manifest["datasets"]["secodeplt"]["status"] = "complete"

    # Save manifest and checksums
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[OK] Saved Download Manifest: {manifest_path.relative_to(root_dir)}")

    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write("\n".join(checksums) + "\n")
    print(f"[OK] Saved SHA256 Checksums: {checksum_path.relative_to(root_dir)}")

    return manifest


if __name__ == "__main__":
    run_full_download()
