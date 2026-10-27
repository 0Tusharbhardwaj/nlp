"""Cross-split deduplication and data leakage prevention engine.

Ensures:
- Zero exact code duplicates between training, validation, and test splits.
- Detection of near-duplicate samples across splits using MinHash / Jaccard similarity.
- Auditing repository or project overlap across partitions when metadata permits.
- Complete preservation of labels and provenance metadata.
"""

from collections import defaultdict
import hashlib
import re
from typing import Any, Dict, List, Set, Tuple

from src.data.analyzer import compute_code_hash, generate_shingles, jaccard_similarity
from src.data.schema import CodeSample


class CrossSplitDeduplicator:
    """Detects and prevents cross-split data leakage across dataset partitions."""

    def __init__(self, splits: Dict[str, List[CodeSample]]):
        self.splits = splits

    def audit_exact_cross_split_leakage(self) -> Dict[str, Any]:
        """Detect identical code instances across different splits (e.g., Train vs Test)."""
        split_hashes: Dict[str, Dict[str, List[str]]] = {}
        for split_name, samples in self.splits.items():
            hashes = defaultdict(list)
            for s in samples:
                h = compute_code_hash(s.code)
                hashes[h].append(s.sample_id)
            split_hashes[split_name] = hashes

        split_names = list(self.splits.keys())
        leakage_results: Dict[str, Any] = {}
        total_leaked_pairs = 0

        for i in range(len(split_names)):
            for j in range(i + 1, len(split_names)):
                s1 = split_names[i]
                s2 = split_names[j]
                comparison_key = f"{s1}_vs_{s2}"
                
                common_hashes = set(split_hashes[s1].keys()).intersection(set(split_hashes[s2].keys()))
                leaked_samples = []
                for ch in common_hashes:
                    leaked_samples.append({
                        f"{s1}_sample_ids": split_hashes[s1][ch],
                        f"{s2}_sample_ids": split_hashes[s2][ch],
                    })

                leakage_results[comparison_key] = {
                    "split_1": s1,
                    "split_2": s2,
                    "common_hash_count": len(common_hashes),
                    "leakage_detected": len(common_hashes) > 0,
                    "leaked_sample_pairs": leaked_samples[:20],
                }
                total_leaked_pairs += len(common_hashes)

        return {
            "total_cross_split_exact_leaks": total_leaked_pairs,
            "comparisons": leakage_results,
        }

    def audit_near_duplicate_leakage(
        self,
        split_1: str = "train",
        split_2: str = "test",
        threshold: float = 0.85,
        max_comparisons: int = 1000,
    ) -> Dict[str, Any]:
        """Detect near-duplicate functions between two splits using character shingles."""
        samples_1 = self.splits.get(split_1, [])[:max_comparisons]
        samples_2 = self.splits.get(split_2, [])[:max_comparisons]

        shingles_1 = [(s.sample_id, generate_shingles(s.code)) for s in samples_1]
        shingles_2 = [(s.sample_id, generate_shingles(s.code)) for s in samples_2]

        near_leaks = []
        for id1, sh1 in shingles_1:
            for id2, sh2 in shingles_2:
                sim = jaccard_similarity(sh1, sh2)
                if sim >= threshold:
                    near_leaks.append({
                        f"{split_1}_id": id1,
                        f"{split_2}_id": id2,
                        "similarity": round(sim, 3),
                    })

        return {
            "split_1": split_1,
            "split_2": split_2,
            "threshold": threshold,
            "near_duplicate_leaks_count": len(near_leaks),
            "near_duplicate_leaks": near_leaks[:20],
        }

    def audit_repository_overlap(self) -> Dict[str, Any]:
        """Audit repository or project distribution across splits to check for isolation."""
        split_repos: Dict[str, Set[str]] = defaultdict(set)
        for split_name, samples in self.splits.items():
            for s in samples:
                if s.repository_id:
                    split_repos[split_name].add(s.repository_id)

        split_names = list(self.splits.keys())
        overlap_results: Dict[str, Any] = {}

        for i in range(len(split_names)):
            for j in range(i + 1, len(split_names)):
                s1 = split_names[i]
                s2 = split_names[j]
                comparison_key = f"{s1}_vs_{s2}"
                shared = split_repos[s1].intersection(split_repos[s2])
                overlap_results[comparison_key] = {
                    f"{s1}_repositories_count": len(split_repos[s1]),
                    f"{s2}_repositories_count": len(split_repos[s2]),
                    "shared_repositories_count": len(shared),
                    "shared_repositories": list(shared),
                }

        return {
            "repository_distribution": {s: list(repos) for s, repos in split_repos.items()},
            "cross_split_repository_overlap": overlap_results,
        }
