# oaFileImportCSV/Tests/test_rust_csv_parser.py
#
# Tests for the CSV Parser (Python vs Rust).
#
# Author: Anthony Peter Kuzub
# Version: 20260331.1600.1

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from oaFileImportCSV.FileReaders.from_csv_unknown import Marker_convert_csv_unknow_report_to_csv

class TestRustCSVParser(unittest.TestCase):
    def setUp(self):
        # Find the sample asset
        self.asset_path = Path(__file__).parent / "Assets" / "Basic_CSV_venue.csv"
        if not self.asset_path.exists():
            # Fallback to absolute path if needed
            self.asset_path = Path("/home/anthony/Documents/OPEN-AIR/oaFileImportCSV/Tests/Assets/Basic_CSV_venue.csv")

    @patch("oaConfiguration.FileReaders.config_reader.Config.get_boolean")
    def test_compare_python_vs_rust_csv(self, mock_get_boolean):
        # 1. Run Python
        mock_get_boolean.return_value = False
        headers_py, data_py = Marker_convert_csv_unknow_report_to_csv(str(self.asset_path))
        self.assertGreater(len(data_py), 0)

        # 2. Run Rust
        mock_get_boolean.return_value = True
        try:
            import oacsvparser_rs
            headers_rs, data_rs = Marker_convert_csv_unknow_report_to_csv(str(self.asset_path))
            
            # 3. Compare Results
            self.assertEqual(headers_py, headers_rs)
            self.assertEqual(len(data_py), len(data_rs))
            
            # Compare first row
            self.assertEqual(data_py[0], data_rs[0])
            
            # Compare all rows for content
            for r_py, r_rs in zip(data_py, data_rs):
                self.assertEqual(r_py, r_rs)
                
        except ImportError:
            self.skipTest("Rust oacsvparser_rs not installed.")

if __name__ == "__main__":
    unittest.main()
