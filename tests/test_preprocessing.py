"""Unit tests for Phase 3 safe preprocessing, token length analysis, and leakage prevention.

Compatible with both unittest and pytest.
"""

from pathlib import Path
import tempfile
import unittest

from src.data.schema import CodeSample
from src.preprocessing import (
    CrossSplitDeduplicator,
    PreprocessingPipeline,
    analyze_token_length_distribution,
    compute_untruncated_token_lengths,
    normalize_whitespace,
    prepare_for_classical_baseline,
    prepare_for_codebert,
    safe_remove_comments,
)


class TestPreprocessing(unittest.TestCase):
    """Test suite verifying safe cleaning, token distributions, and deduplication."""

    def test_safe_comment_remover_preserves_urls_and_strings(self):
        """Verify that safe_remove_comments NEVER corrupts strings, URLs, or escaped quotes."""
        # 1. URL inside string literal
        code_with_url = 'char *url = "http://example.com/v1/api"; // URL definition'
        cleaned_url = safe_remove_comments(code_with_url)
        self.assertIn('"http://example.com/v1/api"', cleaned_url)
        self.assertNotIn("// URL definition", cleaned_url)

        # 2. Block comment delimiter inside string literal
        code_with_fake_comment = 'char *pat = "/* this is inside string */"; /* real comment */'
        cleaned_fake = safe_remove_comments(code_with_fake_comment)
        self.assertIn('"/* this is inside string */"', cleaned_fake)
        self.assertNotIn("/* real comment */", cleaned_fake)

        # 3. Escaped quotes inside strings
        code_with_escaped = 'char *msg = "hello \\"world\\" // inside string";'
        cleaned_escaped = safe_remove_comments(code_with_escaped)
        self.assertIn('"hello \\"world\\" // inside string"', cleaned_escaped)

        # 4. Multi-line block comment
        code_multiline = "int a = 1;\n/* comment line 1\ncomment line 2 */\nint b = 2;"
        cleaned_multiline = safe_remove_comments(code_multiline, preserve_newlines=True)
        self.assertIn("int a = 1;", cleaned_multiline)
        self.assertIn("int b = 2;", cleaned_multiline)
        self.assertNotIn("comment line 1", cleaned_multiline)
        # Verify line count preserved
        self.assertEqual(code_multiline.count("\n"), cleaned_multiline.count("\n"))

    def test_prepare_for_classical_and_codebert(self):
        """Verify distinct preprocessing paths for classical models vs CodeBERT."""
        raw_code = "  int   x  =  10;  // init\n\n\n  return x;  "
        
        # Classical: normalized whitespace, optional comment strip
        classical = prepare_for_classical_baseline(raw_code, strip_comments=True)
        self.assertNotIn("// init", classical)
        self.assertEqual(classical, "int x = 10;\nreturn x;")

        # CodeBERT: structure preserved
        codebert = prepare_for_codebert(raw_code)
        self.assertIn("// init", codebert)
        self.assertTrue(codebert.startswith("int"))

    def test_untruncated_token_lengths(self):
        """Verify token lengths are computed on untruncated code samples."""
        short_code = "int f() { return 1; }"
        # Generate a long function exceeding 512 tokens
        long_body = "    int var_long_identifier_name = 100;\n" * 150
        long_code = f"void big_func() {{\n{long_body}\n}}"

        lengths = compute_untruncated_token_lengths([short_code, long_code])
        self.assertEqual(len(lengths), 2)
        self.assertLess(lengths[0], 50)
        self.assertGreater(lengths[1], 512, "Untruncated length must exceed 512 for long function")

    def test_token_length_distribution_percentiles(self):
        """Verify percentiles and truncation exposure calculations."""
        mock_lengths = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
        stats = analyze_token_length_distribution(mock_lengths, thresholds=[256, 512])

        self.assertEqual(stats["total_samples"], 10)
        self.assertEqual(stats["min_tokens"], 50)
        self.assertEqual(stats["max_tokens"], 900)
        self.assertEqual(stats["median_tokens"], 450.0)

        trunc_512 = stats["truncation_analysis"]["exceeding_512"]
        # Samples > 512: 600, 700, 800, 900 (4 out of 10 = 40%)
        self.assertEqual(trunc_512["exceeding_count"], 4)
        self.assertEqual(trunc_512["exceeding_percentage"], 40.0)

    def test_cross_split_deduplicator(self):
        """Verify detection of exact and near duplicate cross-split leakage."""
        splits_with_leak = {
            "train": [
                CodeSample(sample_id="tr1", source_dataset="t", code="void copy() { int a; }", label=0),
                CodeSample(sample_id="tr2", source_dataset="t", code="void unique_train() { exit(0); }", label=1),
            ],
            "test": [
                # tr1 is leaked into test!
                CodeSample(sample_id="te1", source_dataset="t", code="void copy() { int a; }", label=0),
                CodeSample(sample_id="te2", source_dataset="t", code="void unique_test() { return; }", label=0),
            ],
        }

        dedup = CrossSplitDeduplicator(splits_with_leak)
        leakage = dedup.audit_exact_cross_split_leakage()
        self.assertEqual(leakage["total_cross_split_exact_leaks"], 1)
        self.assertTrue(leakage["comparisons"]["train_vs_test"]["leakage_detected"])

        # Clean splits
        clean_splits = {
            "train": [CodeSample(sample_id="tr1", source_dataset="t", code="void funcA() {}", label=0)],
            "test": [CodeSample(sample_id="te1", source_dataset="t", code="void funcB() {}", label=1)],
        }
        clean_dedup = CrossSplitDeduplicator(clean_splits)
        clean_leakage = clean_dedup.audit_exact_cross_split_leakage()
        self.assertEqual(clean_leakage["total_cross_split_exact_leaks"], 0)

    def test_pipeline_end_to_end(self):
        """Verify PreprocessingPipeline execution and artifact generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)
            pipeline = PreprocessingPipeline(dataset_name="test_ds", output_dir=out_path)

            splits = {
                "train": [
                    CodeSample(
                        sample_id="s1",
                        source_dataset="test_ds",
                        code="int run() { return 0; }",
                        label=0,
                        language="c",
                        provenance="human",
                        split="train",
                    )
                ],
                "test": [
                    CodeSample(
                        sample_id="s2",
                        source_dataset="test_ds",
                        code="void vuln() { char b[10]; strcpy(b, \"str\"); }",
                        label=1,
                        language="c",
                        provenance="human",
                        split="test",
                    )
                ],
            }

            report = pipeline.process_and_save_splits(splits)
            self.assertEqual(report["processed_splits_summary"]["train"], 1)
            self.assertEqual(report["processed_splits_summary"]["test"], 1)
            self.assertIn("token_length_distribution", report)

            # Verify files were created
            train_file = out_path / "train.jsonl"
            test_file = out_path / "test.jsonl"
            summary_file = out_path / "preprocessing_summary.json"
            self.assertTrue(train_file.exists())
            self.assertTrue(test_file.exists())
            self.assertTrue(summary_file.exists())


if __name__ == "__main__":
    unittest.main()
