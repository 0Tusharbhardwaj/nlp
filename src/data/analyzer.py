"""Dataset analysis, quality inspection, and deduplication engine for SecureCode AI.

Implements:
- Missing-value analysis
- Label distribution & imbalance audit
- Language distribution analysis
- Exact duplicate detection (MD5 hash)
- Near-duplicate detection (Character/Token Shingling & MinHash/Jaccard similarity)
- Cross-dataset overlap detection
- Comprehensive summary generation
"""

from collections import Counter, defaultdict
import hashlib
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from src.data.schema import CodeSample


def compute_code_hash(code: str) -> str:
    """Compute an MD5 hash of whitespace-normalized code to detect exact duplicates."""
    normalized = re.sub(r"\s+", " ", code.strip())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def generate_shingles(code: str, k: int = 4) -> Set[str]:
    """Generate k-shingles (character n-grams) from code after stripping excess whitespace."""
    normalized = re.sub(r"\s+", " ", code.strip().lower())
    if len(normalized) < k:
        return {normalized} if normalized else set()
    return {normalized[i:i + k] for i in range(len(normalized) - k + 1)}


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two shingle sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


class DatasetAnalyzer:
    """Analysis and verification toolkit for vulnerability datasets."""

    def __init__(self, samples: List[CodeSample], dataset_name: str = "dataset"):
        self.samples = samples
        self.dataset_name = dataset_name

    def analyze_missing_values(self) -> Dict[str, Dict[str, Any]]:
        """Compute missing/null counts and percentages for all fields."""
        total = len(self.samples)
        fields = [
            "sample_id", "source_dataset", "code", "label",
            "language", "provenance", "repository_id", "cwe_id",
            "label_confidence", "split"
        ]
        
        missing_stats = {}
        for f in fields:
            null_count = sum(1 for s in self.samples if getattr(s, f) is None)
            missing_stats[f] = {
                "missing_count": null_count,
                "missing_percentage": round((null_count / total * 100), 2) if total > 0 else 0.0,
                "present_count": total - null_count,
            }
        return missing_stats

    def analyze_label_distribution(self) -> Dict[str, Any]:
        """Compute binary label counts, class imbalance ratio, and unlabeled samples."""
        total = len(self.samples)
        labels = [s.label for s in self.samples]
        
        class_0_count = sum(1 for label in labels if label == 0)
        class_1_count = sum(1 for label in labels if label == 1)
        null_count = sum(1 for label in labels if label is None)
        labeled_total = class_0_count + class_1_count

        imbalance_ratio = (class_0_count / class_1_count) if class_1_count > 0 else None

        return {
            "total_samples": total,
            "non_vulnerable_count (0)": class_0_count,
            "vulnerable_count (1)": class_1_count,
            "unlabeled_or_ambiguous_count": null_count,
            "vulnerability_rate": round((class_1_count / labeled_total * 100), 2) if labeled_total > 0 else 0.0,
            "class_imbalance_ratio_0_to_1": round(imbalance_ratio, 2) if imbalance_ratio is not None else "N/A",
        }

    def analyze_language_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Compute language breakdown across samples."""
        total = len(self.samples)
        lang_counts = Counter(s.language for s in self.samples)
        
        distribution = {}
        for lang, count in lang_counts.most_common():
            distribution[lang] = {
                "count": count,
                "percentage": round((count / total * 100), 2) if total > 0 else 0.0,
            }
        return distribution

    def detect_exact_duplicates(self) -> Dict[str, Any]:
        """Detect exact duplicate code samples using MD5 content hashing."""
        total = len(self.samples)
        hash_to_ids: Dict[str, List[str]] = defaultdict(list)
        
        for s in self.samples:
            h = compute_code_hash(s.code)
            hash_to_ids[h].append(s.sample_id)

        duplicate_clusters = {h: ids for h, ids in hash_to_ids.items() if len(ids) > 1}
        num_duplicate_samples = sum(len(ids) - 1 for ids in duplicate_clusters.values())

        return {
            "total_samples": total,
            "unique_code_count": len(hash_to_ids),
            "duplicate_sample_count": num_duplicate_samples,
            "duplicate_rate_percentage": round((num_duplicate_samples / total * 100), 2) if total > 0 else 0.0,
            "duplicate_clusters_count": len(duplicate_clusters),
        }

    def detect_near_duplicates(self, threshold: float = 0.85, max_comparisons: int = 5000) -> Dict[str, Any]:
        """Detect near-duplicate code samples based on Jaccard similarity of character shingles.
        
        To prevent O(N^2) explosion on large corpora, comparisons are bounded by max_comparisons.
        """
        num_samples = min(len(self.samples), max_comparisons)
        subset = self.samples[:num_samples]
        shingles_list = [(s.sample_id, generate_shingles(s.code)) for s in subset]

        near_duplicate_pairs: List[Tuple[str, str, float]] = []
        for i in range(num_samples):
            id_a, sh_a = shingles_list[i]
            for j in range(i + 1, num_samples):
                id_b, sh_b = shingles_list[j]
                sim = jaccard_similarity(sh_a, sh_b)
                if sim >= threshold:
                    near_duplicate_pairs.append((id_a, id_b, round(sim, 3)))

        return {
            "evaluated_samples_count": num_samples,
            "threshold": threshold,
            "near_duplicate_pairs_count": len(near_duplicate_pairs),
            "near_duplicate_pairs": near_duplicate_pairs[:50],  # Sample first 50 pairs
        }

    def generate_full_report(self) -> Dict[str, Any]:
        """Aggregate all analyses into a comprehensive dataset summary dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "total_samples": len(self.samples),
            "missing_values": self.analyze_missing_values(),
            "label_distribution": self.analyze_label_distribution(),
            "language_distribution": self.analyze_language_distribution(),
            "exact_duplicates": self.detect_exact_duplicates(),
            "near_duplicates": self.detect_near_duplicates(),
        }


def detect_cross_dataset_overlap(
    dataset_a: List[CodeSample],
    dataset_b: List[CodeSample],
    name_a: str = "Dataset_A",
    name_b: str = "Dataset_B",
    near_dup_threshold: float = 0.90,
    max_near_comparisons: int = 1000,
) -> Dict[str, Any]:
    """Detect exact and near-duplicate leakage between two distinct datasets (e.g., train vs external test)."""
    # 1. Exact match detection via hash table
    hashes_a: Dict[str, List[str]] = defaultdict(list)
    for s in dataset_a:
        hashes_a[compute_code_hash(s.code)].append(s.sample_id)

    exact_matches: List[Dict[str, Any]] = []
    for s in dataset_b:
        h = compute_code_hash(s.code)
        if h in hashes_a:
            exact_matches.append({
                f"{name_a}_sample_ids": hashes_a[h],
                f"{name_b}_sample_id": s.sample_id,
            })

    # 2. Near-duplicate overlap detection
    sub_a = dataset_a[:max_near_comparisons]
    sub_b = dataset_b[:max_near_comparisons]
    shingles_a = [(s.sample_id, generate_shingles(s.code)) for s in sub_a]
    shingles_b = [(s.sample_id, generate_shingles(s.code)) for s in sub_b]

    near_matches: List[Dict[str, Any]] = []
    for id_a, sh_a in shingles_a:
        for id_b, sh_b in shingles_b:
            sim = jaccard_similarity(sh_a, sh_b)
            if sim >= near_dup_threshold:
                near_matches.append({
                    f"{name_a}_id": id_a,
                    f"{name_b}_id": id_b,
                    "similarity": round(sim, 3),
                })

    return {
        "dataset_a": name_a,
        "dataset_b": name_b,
        "count_a": len(dataset_a),
        "count_b": len(dataset_b),
        "exact_matches_count": len(exact_matches),
        "exact_matches": exact_matches[:25],
        "near_duplicate_matches_count": len(near_matches),
        "near_duplicate_matches": near_matches[:25],
    }
