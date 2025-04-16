"""
Unit tests for the DupeRemover functionality.
"""

import unittest
import os
import tempfile
from pathlib import Path
import shutil
import sys
import json

# Import functions from main.py
from main import (
    normalize_line,
    calculate_similarity,
    is_fuzzy_duplicate,
    detect_encoding,
    remove_duplicates,
    generate_report,
)


class TestNormalizeFunction(unittest.TestCase):
    """Tests for the normalize_line function."""

    def test_case_insensitive(self):
        """Test case-insensitive normalization."""
        self.assertEqual(normalize_line("Hello World", "case-insensitive"), "hello world")
        self.assertEqual(normalize_line("HELLO WORLD", "case-insensitive"), "hello world")
        self.assertEqual(normalize_line("hello world", "case-insensitive"), "hello world")

    def test_case_sensitive(self):
        """Test case-sensitive normalization."""
        self.assertEqual(normalize_line("Hello World", "case-sensitive"), "Hello World")
        self.assertEqual(normalize_line("HELLO WORLD", "case-sensitive"), "HELLO WORLD")
        self.assertEqual(normalize_line("hello world", "case-sensitive"), "hello world")

    def test_whitespace_insensitive(self):
        """Test whitespace-insensitive normalization."""
        self.assertEqual(normalize_line("Hello  World", "whitespace-insensitive"), "helloworld")
        self.assertEqual(normalize_line("Hello\tWorld", "whitespace-insensitive"), "helloworld")
        self.assertEqual(normalize_line("Hello\nWorld", "whitespace-insensitive"), "helloworld")

    def test_content_hash(self):
        """Test content-hash normalization."""
        # Same words in different order should have the same hash
        hash1 = normalize_line("Hello World", "content-hash")
        hash2 = normalize_line("World Hello", "content-hash")
        self.assertEqual(hash1, hash2)

    def test_alphanumeric_only(self):
        """Test alphanumeric-only normalization."""
        self.assertEqual(normalize_line("Hello, World!", "alphanumeric-only"), "helloworld")
        self.assertEqual(normalize_line("Hello-World", "alphanumeric-only"), "helloworld")
        self.assertEqual(normalize_line("Hello_123", "alphanumeric-only"), "hello123")


class TestSimilarityFunction(unittest.TestCase):
    """Tests for the calculate_similarity function."""

    def test_identical_strings(self):
        """Test similarity between identical strings."""
        self.assertEqual(calculate_similarity("hello world", "hello world"), 1.0)

    def test_different_strings(self):
        """Test similarity between completely different strings."""
        self.assertEqual(calculate_similarity("hello world", "goodbye universe"), 0.0)

    def test_partial_similarity(self):
        """Test similarity between partially similar strings."""
        # "hello" is common, "world" and "there" are different
        similarity = calculate_similarity("hello world", "hello there")
        self.assertTrue(0 < similarity < 1)
        self.assertAlmostEqual(similarity, 0.5, delta=0.1)

    def test_empty_strings(self):
        """Test similarity with empty strings."""
        self.assertEqual(calculate_similarity("", ""), 1.0)
        self.assertEqual(calculate_similarity("hello", ""), 0.0)


class TestFuzzyDuplicate(unittest.TestCase):
    """Tests for the is_fuzzy_duplicate function."""

    def test_exact_match(self):
        """Test fuzzy matching with exact matches."""
        seen_lines = {"hello world", "goodbye universe"}
        self.assertTrue(is_fuzzy_duplicate("hello world", seen_lines, 0.8))
        self.assertFalse(is_fuzzy_duplicate("hello there", seen_lines, 0.8))

    def test_fuzzy_match_threshold(self):
        """Test fuzzy matching with different thresholds."""
        seen_lines = {"hello world goodbye"}
        # "hello world hi" shares 2/3 words with "hello world goodbye"
        self.assertTrue(is_fuzzy_duplicate("hello world hi", seen_lines, 0.5))
        self.assertFalse(is_fuzzy_duplicate("hello world hi", seen_lines, 0.9))


class TestFileOperations(unittest.TestCase):
    """Tests for file operation functions."""

    def setUp(self):
        """Set up temporary directory and test files."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test file with duplicates
        self.test_file_path = os.path.join(self.temp_dir, "test_duplicates.txt")
        with open(self.test_file_path, "w") as f:
            f.write("Line 1\n")
            f.write("Line 2\n")
            f.write("Line 1\n")  # Duplicate
            f.write("LINE 1\n")  # Case-different duplicate
            f.write("Line 3\n")
        
        # Create an empty file
        self.empty_file_path = os.path.join(self.temp_dir, "empty.txt")
        open(self.empty_file_path, "w").close()

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def test_detect_encoding(self):
        """Test encoding detection."""
        encoding = detect_encoding(self.test_file_path)
        self.assertIn(encoding, ["utf-8", "ascii", "latin-1"])

    def test_remove_duplicates_case_insensitive(self):
        """Test removing duplicates with case-insensitive comparison."""
        result = remove_duplicates(
            self.test_file_path,
            comparison_mode="case-insensitive",
            show_progress=False,
            dry_run=True
        )
        
        self.assertEqual(result["total_lines"], 5)
        self.assertEqual(result["unique_lines"], 3)
        self.assertEqual(result["duplicates_removed"], 2)

    def test_remove_duplicates_case_sensitive(self):
        """Test removing duplicates with case-sensitive comparison."""
        result = remove_duplicates(
            self.test_file_path,
            comparison_mode="case-sensitive",
            show_progress=False,
            dry_run=True
        )
        
        self.assertEqual(result["total_lines"], 5)
        self.assertEqual(result["unique_lines"], 4)
        self.assertEqual(result["duplicates_removed"], 1)

    def test_empty_file(self):
        """Test processing an empty file."""
        result = remove_duplicates(
            self.empty_file_path,
            show_progress=False,
            dry_run=True
        )
        
        self.assertEqual(result["total_lines"], 0)
        self.assertEqual(result["unique_lines"], 0)
        self.assertEqual(result["duplicates_removed"], 0)


class TestReportGeneration(unittest.TestCase):
    """Tests for the generate_report function."""
    
    def setUp(self):
        """Set up sample results for testing reports."""
        self.sample_results = [
            {
                "file_path": "test_file1.txt",
                "total_lines": 100,
                "unique_lines": 80,
                "duplicates_removed": 20,
                "dry_run": False
            },
            {
                "file_path": "test_file2.txt",
                "total_lines": 50,
                "unique_lines": 40,
                "duplicates_removed": 10,
                "dry_run": True
            },
            {
                "file_path": "error_file.txt",
                "error": "File not found"
            }
        ]
    
    def test_text_report_generation(self):
        """Test generating a text report."""
        report = generate_report(self.sample_results, "text")
        self.assertIn("=== DupeRemover Results ===", report)
        self.assertIn("Files processed: 2/3", report)
        self.assertIn("Files failed: 1", report)
        self.assertIn("test_file1.txt", report)
        self.assertIn("test_file2.txt", report)
        self.assertIn("error_file.txt", report)
        self.assertIn("Total lines: 100", report)
        self.assertIn("[ERROR]", report)
        
    def test_colored_text_report(self):
        """Test generating a colored text report."""
        report = generate_report(self.sample_results, "text", use_color=True)
        self.assertIn("\033[", report)  # ANSI color codes should be present
        self.assertIn("\033[1m", report)  # Bold text
        self.assertIn("\033[92m", report)  # Green color
        self.assertIn("\033[93m", report)  # Yellow color
        self.assertIn("\033[91m", report)  # Red color for errors
        
    def test_json_report_generation(self):
        """Test generating a JSON report."""
        report = generate_report(self.sample_results, "json")
        self.assertIn('"timestamp":', report)
        self.assertIn('"summary":', report)
        self.assertIn('"results":', report)
        self.assertIn('"files_processed": 2', report)
        self.assertIn('"files_failed": 1', report)
        
        # Validate that it's valid JSON
        report_dict = json.loads(report)
        self.assertEqual(len(report_dict["results"]), 3)
        
    def test_csv_report_generation(self):
        """Test generating a CSV report."""
        report = generate_report(self.sample_results, "csv")
        self.assertIn("DupeRemover Results", report)
        self.assertIn("SUMMARY", report)
        self.assertIn("Files processed,2/3", report)
        self.assertIn("File,Total Lines,Unique Lines,Duplicates Removed,Duplication Rate,Status", report)
        self.assertIn("test_file1.txt,100,80,20,20.00%,Success", report)
        self.assertIn("test_file2.txt,50,40,10,20.00%,Dry run", report)
        self.assertIn("ERROR: File not found", report)


if __name__ == "__main__":
    unittest.main() 