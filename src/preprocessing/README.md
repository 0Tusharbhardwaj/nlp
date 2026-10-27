# SecureCode AI — Data Preprocessing Documentation

## 1. Overview & Core Philosophy

The SecureCode AI preprocessing pipeline prepares source code for two distinct modeling paradigms while guaranteeing scientific reproducibility and preventing data leakage:

1. **Classical Lexical Baselines (TF-IDF + LR / SVM)**: Requires controlled token normalization, optional safe comment stripping, and whitespace standardization.
2. **Deep Contextual Transformers (CodeBERT)**: Requires raw code syntax, structure, variable identifiers, and brackets to remain intact. CodeBERT's BPE tokenizer relies on code grammar to construct contextual semantic representations.

---

## 2. Key Preprocessing Components

### 2.1 State-Machine Safe Cleaner (`safe_cleaner.py`)
- **The Problem with Naive Regex**: Standard regex comment strippers like `re.sub(r"//.*", "", code)` corrupt URLs (e.g. `"http://api.example.com"` becomes `"http:`) and multi-line strings containing comment delimiters.
- **The Solution**: A robust 5-state lexer (`NORMAL`, `IN_STRING`, `IN_CHAR`, `IN_LINE_COMMENT`, `IN_BLOCK_COMMENT`) that preserves:
  - String literals containing `//`, `/*`, or `*/`
  - Escaped quotes (`\"`) and character literals (`'\''`)
  - URLs and regex patterns
  - Newlines within comments (to preserve line numbering)

### 2.2 Untruncated Token-Length Distribution (`tokenizer_utils.py`)
- **Scientific Requirement**: Token lengths are computed on the **complete, untruncated** code snippet using the actual tokenizer before any truncation to 512.
- **Reporting**: Computes min, max, mean, median, P75, P90, P95, and P99 percentiles, explicitly quantifying what percentage of functions exceed candidate sequence windows (128, 256, 512, 1024).

### 2.3 Cross-Split Deduplication & Leakage Prevention (`deduplicator.py`)
- Audits MD5 content hashes across partitions (`train_vs_valid`, `train_vs_test`, `valid_vs_test`).
- Audits MinHash / Jaccard near-duplicate functions across splits.
- Inspects repository / project distribution across partitions.

---

## 3. Preprocessed Record Schema

Preprocessed records stored in `datasets/processed/<dataset_name>/<split>.jsonl` adhere to:

```json
{
  "sample_id": "devign_train_1001",
  "source_dataset": "devign",
  "raw_code": "static void bad_buffer_copy(...) { ... }",
  "classical_code": "static void bad_buffer_copy(...) { ... }",
  "codebert_code": "static void bad_buffer_copy(...) { ... }",
  "label": 1,
  "language": "c",
  "provenance": "human",
  "repository_id": "qemu",
  "cwe_id": null,
  "label_confidence": 1.0,
  "split": "train",
  "untruncated_token_length": 34,
  "exceeds_512_tokens": false,
  "metadata": {
    "original_id": 1001,
    "commit_id": "2a18b746..."
  }
}
```

---

## 4. Running the Preprocessing Pipeline

Run the preprocessing pipeline from the command line:

```bash
python scripts/preprocess_data.py --config configs/preprocessing.yaml
```

The script will:
1. Ingest datasets defined in `configs/preprocessing.yaml`.
2. Generate preprocessed partitions in `datasets/processed/<dataset>/`.
3. Output the comprehensive audit report in `datasets/reports/PREPROCESSING_REPORT.md`.
