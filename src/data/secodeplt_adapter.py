"""SECODEPLT Benchmark Evaluation Adapter for Vulnerability Detection.

Adapts the UCSB-SURFI SeCodePLT C vulnerability detection benchmark into
standardized (code, label, metadata) evaluation pairs without forcing or polluting
the CodeXGLUE/Devign binary training cohort.

Task formulation:
Each SeCodePLT task contains:
- in_function_context: Function template containing placeholder '##SECCODEPLT##'
- vulnerable_code_reference: Original vulnerable implementation (Label: 1)
- patched_code_reference: Patched secure implementation (Label: 0)
- CWE_ID: Associated Common Weakness Enumeration
- meta_data: Commit hash, target function, file, and Docker verification image
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pyarrow.parquet as pq


class SeCodePLTAdapter:
    """Evaluation adapter for SeCodePLT C Vulnerability Detection benchmark."""

    PLACEHOLDER = "##SECCODEPLT##"

    def __init__(self, raw_path: Optional[Path] = None):
        if raw_path is None:
            # Default location in full-scale raw datasets
            project_root = Path(__file__).resolve().parent.parent.parent
            parquet_path = project_root / "datasets" / "raw" / "full" / "secodeplt" / "c_vulnerability_detection.parquet"
            jsonl_path = project_root / "datasets" / "raw" / "full" / "secodeplt" / "c_vulnerability_detection.jsonl"
            self.raw_path = parquet_path if parquet_path.exists() else jsonl_path
        else:
            self.raw_path = Path(raw_path)

    def load_raw_records(self) -> List[Dict[str, Any]]:
        """Load raw SeCodePLT records from parquet or JSONL."""
        if not self.raw_path.exists():
            raise FileNotFoundError(f"SeCodePLT dataset file not found: {self.raw_path}")

        records: List[Dict[str, Any]] = []
        if self.raw_path.suffix == ".parquet":
            table = pq.read_table(self.raw_path)
            for i in range(table.num_rows):
                rec = {col: table.column(col)[i].as_py() for col in table.column_names}
                records.append(rec)
        else:
            with open(self.raw_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        return records

    def adapt_samples(self) -> List[Dict[str, Any]]:
        """Adapt raw records into standardized binary classification evaluation instances.
        
        For each record:
        - Creates 1 vulnerable instance (target = 1)
        - Creates 1 patched secure instance (target = 0)
        
        Returns:
            List of dictionaries with keys:
            ['id', 'code', 'target', 'task_id', 'cwe_id', 'variant', 'metadata']
        """
        raw_records = self.load_raw_records()
        evaluation_samples: List[Dict[str, Any]] = []

        for rec in raw_records:
            task_id = str(rec.get("id", ""))
            template = str(rec.get("in_function_context", ""))
            vuln_ref = str(rec.get("vulnerable_code_reference", ""))
            patch_ref = str(rec.get("patched_code_reference", ""))
            cwe_id = str(rec.get("CWE_ID", "")).strip()
            
            raw_meta = rec.get("meta_data", "")
            meta_dict = json.loads(raw_meta) if isinstance(raw_meta, str) and raw_meta else (raw_meta or {})

            if self.PLACEHOLDER not in template:
                # If placeholder is not found, fallback to standalone references
                vuln_code = vuln_ref if vuln_ref else template
                patch_code = patch_ref if patch_ref else template
            else:
                vuln_code = template.replace(self.PLACEHOLDER, vuln_ref)
                patch_code = template.replace(self.PLACEHOLDER, patch_ref)

            # Instance 1: Vulnerable reference
            evaluation_samples.append({
                "id": f"secodeplt_{task_id}_vuln",
                "task_id": task_id,
                "variant": "vulnerable",
                "code": vuln_code.strip(),
                "target": 1,
                "cwe_id": cwe_id if cwe_id else None,
                "language": "c",
                "provenance": "synthetic:ground_truth_cve",
                "metadata": {
                    "target_function": meta_dict.get("target_function"),
                    "target_file": meta_dict.get("target_file"),
                    "fix_commit": meta_dict.get("fix_commit"),
                    "workdir": meta_dict.get("workdir"),
                },
            })

            # Instance 2: Patched reference
            evaluation_samples.append({
                "id": f"secodeplt_{task_id}_patch",
                "task_id": task_id,
                "variant": "patched",
                "code": patch_code.strip(),
                "target": 0,
                "cwe_id": cwe_id if cwe_id else None,
                "language": "c",
                "provenance": "synthetic:ground_truth_patch",
                "metadata": {
                    "target_function": meta_dict.get("target_function"),
                    "target_file": meta_dict.get("target_file"),
                    "fix_commit": meta_dict.get("fix_commit"),
                    "workdir": meta_dict.get("workdir"),
                },
            })

        return evaluation_samples

    def export_evaluation_jsonl(self, output_path: Path) -> int:
        """Export standardized evaluation cohort to JSONL."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        samples = self.adapt_samples()
        with open(output_path, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s) + "\n")
        return len(samples)


if __name__ == "__main__":
    adapter = SeCodePLTAdapter()
    samples = adapter.adapt_samples()
    print(f"[OK] SeCodePLT Adapter generated {len(samples)} evaluation instances from {len(samples)//2} tasks.")
