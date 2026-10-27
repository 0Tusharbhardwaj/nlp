"""CLI script to execute the reproducible preprocessing pipeline.

Generates preprocessed partitions in datasets/processed/ and audits
token length distributions, truncation statistics (>512), and cross-split leakage in datasets/reports/.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict
import yaml

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.data import (
    DevignDatasetLoader,
    LLMVulDatasetLoader,
    SeCodePLTDatasetLoader,
)
from src.preprocessing import PreprocessingPipeline
from src.utils.config import get_project_root


def generate_markdown_report(all_reports: Dict[str, Any]) -> str:
    """Generate comprehensive Markdown preprocessing report."""
    lines = [
        "# SecureCode AI — Data Preprocessing & Token-Length Audit Report",
        "",
        "## 1. Executive Summary",
        "",
        "This report documents the preprocessing results across evaluated vulnerability benchmarks.",
        "Crucially, **token lengths are calculated on complete, untruncated code samples** before",
        "applying any sequence bounds, allowing precise quantification of truncation exposure.",
        "",
        "---",
        "",
        "## 2. Token-Length Distribution & Truncation Audit (>512 Tokens)",
        "",
        "| Dataset | Total Samples | Min | Max | Mean | Median | P90 | P95 | P99 | Exceeding 512 (%) | Exceeding 256 (%) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for name, rep in all_reports.items():
        t = rep.get("token_length_distribution", {})
        trunc = t.get("truncation_analysis", {})
        exc_512 = trunc.get("exceeding_512", {}).get("exceeding_percentage", 0.0)
        exc_256 = trunc.get("exceeding_256", {}).get("exceeding_percentage", 0.0)
        
        lines.append(
            f"| **{name.upper()}** | {t.get('total_samples', 0)} | {t.get('min_tokens', 0)} | "
            f"{t.get('max_tokens', 0)} | {t.get('mean_tokens', 0)} | {t.get('median_tokens', 0)} | "
            f"{t.get('p90_tokens', 0)} | {t.get('p95_tokens', 0)} | {t.get('p99_tokens', 0)} | "
            f"**{exc_512}%** | {exc_256}% |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Cross-Split Leakage & Deduplication Audit",
        "",
    ])

    for name, rep in all_reports.items():
        leakage = rep.get("cross_split_leakage_audit", {})
        total_leaks = leakage.get("total_cross_split_exact_leaks", 0)
        lines.append(f"### Dataset: `{name.upper()}`")
        lines.append(f"- **Total Exact Cross-Split Leaks:** {total_leaks}")
        
        comparisons = leakage.get("comparisons", {})
        if comparisons:
            for comp_name, comp_data in comparisons.items():
                status = "CLEAN (0 leaks)" if not comp_data["leakage_detected"] else f"WARNING ({comp_data['common_hash_count']} leaks)"
                lines.append(f"  - `{comp_name}`: {status}")
        else:
            lines.append("  - *Single external partition; cross-split comparison not applicable.*")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Preprocessed Partitions Summary",
        "",
        "| Dataset | Partitions Saved | Storage Location |",
        "| :--- | :--- | :--- |",
    ])
    for name, rep in all_reports.items():
        splits_str = ", ".join([f"{k} ({v})" for k, v in rep.get("processed_splits_summary", {}).items()])
        lines.append(f"| `{name}` | {splits_str} | `datasets/processed/{name}/` |")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run SecureCode AI Preprocessing Pipeline.")
    parser.add_argument("--config", type=str, default="configs/preprocessing.yaml", help="Path to preprocessing config.")
    args = parser.parse_args()

    project_root = get_project_root()
    config_path = project_root / args.config
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print("=================================================================")
    print(" SecureCode AI - Data Preprocessing & Token-Length Audit Pipeline")
    print("=================================================================")

    loaders = {
        "devign": DevignDatasetLoader(),
        "llmvul": LLMVulDatasetLoader(),
        "secodeplt": SeCodePLTDatasetLoader(),
    }

    all_reports: Dict[str, Any] = {}

    for name, loader in loaders.items():
        ds_config = config.get("datasets", {}).get(name, {})
        if not ds_config.get("enabled", True):
            print(f"Skipping {name} (disabled in config).")
            continue

        print(f"\nProcessing dataset: [{name.upper()}]...")
        pipeline = PreprocessingPipeline(dataset_name=name, config=ds_config)
        splits = loader.get_splits()
        
        report = pipeline.process_and_save_splits(splits)
        all_reports[name] = report
        print(f"  -> Processed {sum(report['processed_splits_summary'].values())} samples.")
        print(f"  -> Mean untruncated token length: {report['token_length_distribution']['mean_tokens']} tokens.")
        print(f"  -> Samples exceeding 512 tokens: {report['token_length_distribution']['truncation_analysis']['exceeding_512']['exceeding_count']} "
              f"({report['token_length_distribution']['truncation_analysis']['exceeding_512']['exceeding_percentage']}%)")

    # Generate Markdown and JSON reports in datasets/reports/
    reports_dir = project_root / "datasets" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_report_path = reports_dir / "preprocessing_summary.json"
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(all_reports, f, indent=2)

    md_report_path = reports_dir / "PREPROCESSING_REPORT.md"
    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(generate_markdown_report(all_reports))

    print(f"\n[SUCCESS] Preprocessing complete. Reports saved to:")
    print(f"  - {md_report_path}")
    print(f"  - {json_report_path}")


if __name__ == "__main__":
    main()
