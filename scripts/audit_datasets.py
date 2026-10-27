"""Dataset Audit and Summary Reporting Script for SecureCode AI.

Runs quality inspection, missing-value analysis, label distribution, exact/near-duplicate
detection, and cross-dataset overlap analysis across all candidate datasets.
Outputs structured JSON and Markdown audit reports in datasets/reports/.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.data import (
    CodeSample,
    DatasetAnalyzer,
    DevignDatasetLoader,
    HumanVsAICodeDatasetLoader,
    LLMVulDatasetLoader,
    SeCodePLTDatasetLoader,
    detect_cross_dataset_overlap,
)
from src.utils.config import get_project_root


def format_markdown_report(report_data: Dict[str, Any]) -> str:
    """Format dictionary analysis output into a readable Markdown report."""
    name = report_data["dataset_name"]
    total = report_data["total_samples"]
    labels = report_data["label_distribution"]
    missing = report_data["missing_values"]
    exact_dups = report_data["exact_duplicates"]
    near_dups = report_data["near_duplicates"]
    languages = report_data["language_distribution"]

    lines = [
        f"# Dataset Audit Report: {name.upper()}",
        "",
        f"- **Total Samples:** {total}",
        f"- **Vulnerability Rate:** {labels.get('vulnerability_rate', 0)}%",
        f"- **Class 0 (Non-Vulnerable):** {labels.get('non_vulnerable_count (0)', 0)}",
        f"- **Class 1 (Vulnerable):** {labels.get('vulnerable_count (1)', 0)}",
        f"- **Unlabeled / Ambiguous:** {labels.get('unlabeled_or_ambiguous_count', 0)}",
        f"- **Class Imbalance Ratio (0 to 1):** {labels.get('class_imbalance_ratio_0_to_1', 'N/A')}",
        "",
        "## Language Distribution",
        "| Language | Count | Percentage |",
        "| :--- | :--- | :--- |",
    ]
    for lang, stats in languages.items():
        lines.append(f"| {lang} | {stats['count']} | {stats['percentage']}% |")

    lines.extend([
        "",
        "## Missing-Value Analysis",
        "| Field | Missing Count | Missing % | Present Count |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for field_name, stats in missing.items():
        lines.append(f"| `{field_name}` | {stats['missing_count']} | {stats['missing_percentage']}% | {stats['present_count']} |")

    lines.extend([
        "",
        "## Duplication Analysis",
        f"- **Unique Code Hashes:** {exact_dups.get('unique_code_count', 0)}",
        f"- **Exact Duplicate Samples:** {exact_dups.get('duplicate_sample_count', 0)} ({exact_dups.get('duplicate_rate_percentage', 0)}%)",
        f"- **Exact Duplicate Clusters:** {exact_dups.get('duplicate_clusters_count', 0)}",
        f"- **Evaluated Samples for Near-Duplicates:** {near_dups.get('evaluated_samples_count', 0)}",
        f"- **Near-Duplicate Pairs Detected (Threshold >= {near_dups.get('threshold', 0.85)}):** {near_dups.get('near_duplicate_pairs_count', 0)}",
        "",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit and report dataset quality metrics.")
    parser.add_argument("--output-dir", type=str, default="datasets/reports", help="Directory to save audit reports.")
    parser.add_argument("--near-dup-threshold", type=float, default=0.85, help="Jaccard threshold for near duplicates.")
    args = parser.parse_args()

    project_root = get_project_root()
    output_dir = project_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print(" SecureCode AI - Dataset Engineering Audit & Quality Inspection ")
    print("=================================================================")

    # Initialize loaders
    devign_loader = DevignDatasetLoader()
    llmvul_loader = LLMVulDatasetLoader()
    secodeplt_loader = SeCodePLTDatasetLoader()
    human_vs_ai_loader = HumanVsAICodeDatasetLoader()

    loaders = {
        "devign": devign_loader,
        "llmvul": llmvul_loader,
        "secodeplt": secodeplt_loader,
        "human_vs_ai": human_vs_ai_loader,
    }

    loaded_datasets: Dict[str, List[CodeSample]] = {}

    for name, loader in loaders.items():
        samples = loader.load()
        loaded_datasets[name] = samples
        print(f"[{name.upper()}] Loaded {len(samples)} samples from raw cache.")

        analyzer = DatasetAnalyzer(samples, dataset_name=name)
        report = analyzer.generate_full_report()

        # Save JSON
        json_path = output_dir / f"{name}_audit.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Save Markdown
        md_path = output_dir / f"{name}_audit.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(format_markdown_report(report))

        print(f"  -> Generated audit report: {md_path.name}")

    # Cross-dataset overlap audit between Devign and LLMVul
    if loaded_datasets["devign"] and loaded_datasets["llmvul"]:
        print("\nChecking cross-dataset leakage between Devign and LLMVul...")
        overlap = detect_cross_dataset_overlap(
            loaded_datasets["devign"],
            loaded_datasets["llmvul"],
            name_a="Devign",
            name_b="LLMVul",
            near_dup_threshold=0.90,
        )
        overlap_path = output_dir / "devign_vs_llmvul_overlap.json"
        with open(overlap_path, "w", encoding="utf-8") as f:
            json.dump(overlap, f, indent=2)
        print(f"  -> Cross-dataset overlap report saved to {overlap_path.name}")
        print(f"  -> Exact matches: {overlap['exact_matches_count']}, Near duplicates: {overlap['near_duplicate_matches_count']}")

    print("\n[SUCCESS] Dataset audit and summary generation complete.")


if __name__ == "__main__":
    main()
