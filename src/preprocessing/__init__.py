"""Code preprocessing, token length analysis, and leakage prevention package."""

from .deduplicator import CrossSplitDeduplicator
from .pipeline import PreprocessingPipeline
from .safe_cleaner import (
    normalize_whitespace,
    prepare_for_classical_baseline,
    prepare_for_codebert,
    safe_remove_comments,
)
from .tokenizer_utils import (
    analyze_token_length_distribution,
    compute_untruncated_token_lengths,
    get_codebert_tokenizer,
)

__all__ = [
    "safe_remove_comments",
    "normalize_whitespace",
    "prepare_for_classical_baseline",
    "prepare_for_codebert",
    "get_codebert_tokenizer",
    "compute_untruncated_token_lengths",
    "analyze_token_length_distribution",
    "CrossSplitDeduplicator",
    "PreprocessingPipeline",
]
