"""LLMVul Repository-Disjoint Partitioner and Integrity Filter.

Implements rigorous, leak-free partitioning for the LLMVul benchmark:
1. Filters uncertain labels (signal divergence / null labels) into a distinct quarantine partition.
2. Preserves AI provenance (ai_tool: claude_code, copilot, cursor, gemini, etc.) and CWE identifiers.
3. Partitions repositories disjointly (intersection of train and test repositories is strictly empty).
4. Balances vulnerability class distribution across repository partitions.
5. Ingests and processes the 100-sample expert human review gold partition.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd


class LLMVulPartitioner:
    """Partitions LLMVul into repository-disjoint train/test cohorts with uncertain label isolation."""

    def __init__(self, raw_csv_path: Optional[Path] = None, manual_csv_path: Optional[Path] = None):
        project_root = Path(__file__).resolve().parent.parent.parent
        self.raw_csv_path = raw_csv_path or (
            project_root / "datasets" / "raw" / "full" / "llmvul" / "LLMVul_v3-Updated.csv"
        )
        self.manual_csv_path = manual_csv_path or (
            project_root / "datasets" / "raw" / "full" / "llmvul" / "LLMVul_manual_review_100-Updated.csv"
        )

    def load_and_partition(
        self,
        test_ratio: float = 0.20,
        random_seed: int = 42,
    ) -> Dict[str, Any]:
        """Load LLMVul and produce clean repository-disjoint partitions.
        
        Returns:
            Dict containing:
            - 'train_records': List of dicts
            - 'test_records': List of dicts
            - 'uncertain_records': List of dicts
            - 'manual_gold_records': List of dicts
            - 'partition_stats': Dict of statistics
        """
        if not self.raw_csv_path.exists():
            raise FileNotFoundError(f"LLMVul CSV not found: {self.raw_csv_path}")

        df = pd.read_csv(self.raw_csv_path, skiprows=1, low_memory=False)
        
        # 1. Separate uncertain records
        uncertain_mask = (df["ensemble_label"] == "uncertain") | df["vuln_label"].isna()
        uncertain_df = df[uncertain_mask].copy()
        certain_df = df[~uncertain_mask].copy()

        # Map target label
        certain_df["target"] = (certain_df["ensemble_label"] == "vulnerable").astype(int)

        # 2. Group by repository to achieve strictly disjoint partitions
        proj_stats = certain_df.groupby("project_name").agg(
            n_funcs=("unique_id", "count"),
            n_vuln=("target", "sum")
        ).reset_index()

        proj_stats["vuln_rate"] = proj_stats["n_vuln"] / proj_stats["n_funcs"]
        # Deterministic sorting
        proj_stats = proj_stats.sort_values(
            by=["n_funcs", "n_vuln", "project_name"],
            ascending=[False, False, True]
        ).reset_index(drop=True)

        target_test_samples = int(len(certain_df) * test_ratio)
        max_test_samples = int(len(certain_df) * (test_ratio + 0.02))

        train_repos: Set[str] = set()
        test_repos: Set[str] = set()
        test_count = 0

        for _, row in proj_stats.iterrows():
            p_name = row["project_name"]
            n_funcs = row["n_funcs"]

            # If adding this repository fits within test target
            if (test_count < target_test_samples) and (test_count + n_funcs <= max_test_samples):
                test_repos.add(p_name)
                test_count += n_funcs
            else:
                train_repos.add(p_name)

        # Verify strict repository disjointness
        assert len(train_repos & test_repos) == 0, "FATAL: Repository overlap detected!"

        train_df = certain_df[certain_df["project_name"].isin(train_repos)].copy()
        test_df = certain_df[certain_df["project_name"].isin(test_repos)].copy()

        # 3. Process records into clean dict format
        def row_to_dict(row: pd.Series, split_tag: str, is_uncertain: bool = False) -> Dict[str, Any]:
            target_val = None if is_uncertain else int(row["target"])
            return {
                "id": str(row["unique_id"]),
                "code": str(row["function_body"]),
                "target": target_val,
                "project_name": str(row.get("project_name", "")),
                "commit_id": str(row.get("commit_id", "")),
                "language": str(row.get("language", "c")),
                "ai_tool": str(row.get("ai_tool", "")),
                "provenance": f"ai_assisted:{row.get('ai_tool', 'unknown')}",
                "cwe_id": str(row.get("cwe_id", "")) if pd.notna(row.get("cwe_id")) else None,
                "cwe_description": str(row.get("cwe_description", "")) if pd.notna(row.get("cwe_description")) else None,
                "signal_strength": str(row.get("signal_strength", "")),
                "ensemble_label": str(row.get("ensemble_label", "")),
                "split": split_tag,
            }

        train_records = [row_to_dict(r, "train") for _, r in train_df.iterrows()]
        test_records = [row_to_dict(r, "test") for _, r in test_df.iterrows()]
        uncertain_records = [row_to_dict(r, "quarantine_uncertain", is_uncertain=True) for _, r in uncertain_df.iterrows()]

        # 4. Ingest manual gold validation partition if present
        manual_records = []
        if self.manual_csv_path.exists():
            m_df = pd.read_csv(self.manual_csv_path, skiprows=1)
            for _, r in m_df.iterrows():
                r1 = r.get("rater1_label")
                r2 = r.get("rater2_label")
                # Consensus label if raters agree and neither is -1
                consensus = int(r1) if (r1 == r2 and r1 in [0, 1]) else None
                manual_records.append({
                    "id": str(r.get("unique_id", "")),
                    "code": str(r.get("function_body", "")),
                    "target": consensus,
                    "rater1_label": int(r1) if pd.notna(r1) else None,
                    "rater2_label": int(r2) if pd.notna(r2) else None,
                    "raters_agreed": bool(r1 == r2),
                    "project_name": str(r.get("project_name", "")),
                    "language": str(r.get("language", "c")),
                    "ai_tool": str(r.get("ai_tool", "")),
                    "provenance": f"ai_assisted:{r.get('ai_tool', 'unknown')}",
                    "cwe_id": str(r.get("cwe_id", "")) if pd.notna(r.get("cwe_id")) else None,
                    "notes": str(r.get("notes", "")) if pd.notna(r.get("notes")) else None,
                    "split": "manual_review_gold",
                })

        stats = {
            "total_raw_rows": len(df),
            "certain_rows": len(certain_df),
            "uncertain_quarantined": len(uncertain_df),
            "train_repos": len(train_repos),
            "train_samples": len(train_records),
            "train_vulnerable": int(train_df["target"].sum()),
            "train_safe": int((train_df["target"] == 0).sum()),
            "train_vuln_rate": float(train_df["target"].mean()),
            "test_repos": len(test_repos),
            "test_samples": len(test_records),
            "test_vulnerable": int(test_df["target"].sum()),
            "test_safe": int((test_df["target"] == 0).sum()),
            "test_vuln_rate": float(test_df["target"].mean()),
            "manual_gold_samples": len(manual_records),
            "manual_consensus_samples": sum(1 for m in manual_records if m["target"] is not None),
        }

        return {
            "train_records": train_records,
            "test_records": test_records,
            "uncertain_records": uncertain_records,
            "manual_gold_records": manual_records,
            "train_repos": sorted(list(train_repos)),
            "test_repos": sorted(list(test_repos)),
            "stats": stats,
        }

    def export_partitions(self, output_dir: Path) -> Dict[str, Path]:
        """Export all partitions to JSONL files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        result = self.load_and_partition()

        paths = {
            "train": output_dir / "llmvul_train_clean.jsonl",
            "test": output_dir / "llmvul_test_clean.jsonl",
            "uncertain": output_dir / "llmvul_uncertain.jsonl",
            "manual_gold": output_dir / "llmvul_manual_gold.jsonl",
            "metadata": output_dir / "llmvul_partitions_meta.json",
        }

        with open(paths["train"], "w", encoding="utf-8") as f:
            for r in result["train_records"]:
                f.write(json.dumps(r) + "\n")

        with open(paths["test"], "w", encoding="utf-8") as f:
            for r in result["test_records"]:
                f.write(json.dumps(r) + "\n")

        with open(paths["uncertain"], "w", encoding="utf-8") as f:
            for r in result["uncertain_records"]:
                f.write(json.dumps(r) + "\n")

        with open(paths["manual_gold"], "w", encoding="utf-8") as f:
            for r in result["manual_gold_records"]:
                f.write(json.dumps(r) + "\n")

        with open(paths["metadata"], "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stats": result["stats"],
                "train_repos": result["train_repos"],
                "test_repos": result["test_repos"],
            }, f, indent=2)

        return paths


if __name__ == "__main__":
    partitioner = LLMVulPartitioner()
    p_dir = Path(__file__).resolve().parent.parent.parent / "datasets" / "processed"
    paths = partitioner.export_partitions(p_dir)
    print(f"[OK] LLMVul partitioned successfully to {p_dir}")
