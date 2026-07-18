# ==========================================
# Header: test_rust_csv_parser.py
# Purpose: test_rust_csv_parser.py implementation.
# Description: Logic and implementation for test_rust_csv_parser.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

# oaFileHandlers/oaFileImportCSV/Tests/test_rust_csv_parser.py
#
# Tests for the CSV Parser (Rust implementation).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import unittest
from pathlib import Path

from oaFileHandlers.oaFileImportCSV.FileReaders.from_csv_unknown import Marker_convert_csv_unknow_report_to_csv


class TestRustCSVParser(unittest.TestCase):
    def setUp(self):
        # Find the sample asset
        self.asset_path = Path(__file__).parent / "Assets" / "Basic_CSV_venue.csv"
        if not self.asset_path.exists():
            # No absolute fallback: the old one pointed at a repo layout that no
            # longer exists, so it turned a missing asset into a confusing error
            # about someone else's home directory. Fail with the path we wanted.
            self.skipTest(f"sample asset not found: {self.asset_path}")


    def test_rust_csv_parsing(self):
        """Test CSV parsing with the mandatory Rust backend."""
        try:
            from oaRustCore import oa_csv_parser_rs as oacsvparser_rs
        except ImportError:
            self.skipTest("Rust oacsvparser_rs not installed.")

        headers, data = Marker_convert_csv_unknow_report_to_csv(str(self.asset_path))

        self.assertGreater(len(data), 0)
        # Verify we have some standard headers (e.g., ZONE, NAME, FREQ_MHZ)
        self.assertIn("ZONE", headers)
        self.assertIn("NAME", headers)
        self.assertIn("FREQ_MHZ", headers)

        # Verify data structure
        for row in data:
            self.assertEqual(len(row), len(headers))

if __name__ == "__main__":
    unittest.main()
