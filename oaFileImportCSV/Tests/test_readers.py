# oaFileImportCSV/Tests/test_readers.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Unit tests for the CSV file reader.

import unittest
import os
import pathlib
from oaFileImportCSV.FileReaders.from_csv_unknown import Marker_convert_csv_unknow_report_to_csv

class TestCSVReader(unittest.TestCase):
    """
    Tests the CSV reader module.
    Follows the F.I.R.S.T principles and BUILD-OPERATE-CHECK pattern.
    """

    def setUp(self):
        """BUILD: Define paths for test assets."""
        self.test_dir = pathlib.Path(__file__).resolve().parent
        self.sample_file = self.test_dir / "Assets" / "sample.csv"

    def test_csv_reader_functional(self):
        """OPERATE & CHECK: Verify the CSV reader correctly processes a sample file."""
        # BUILD
        # (sample_file path defined in setUp)

        # OPERATE
        headers, data = Marker_convert_csv_unknow_report_to_csv(str(self.sample_file))

        # CHECK
        self.assertTrue(len(headers) > 0, "Headers should be returned")
        self.assertTrue(len(data) == 2, "Data should contain 2 rows")
        
        # Verify first row data mapping
        first_row = data[0]
        self.assertEqual(first_row["ZONE"], "Zone1")
        self.assertEqual(first_row["NAME"], "Name1")
        self.assertEqual(first_row["FREQ_MHZ"], 500.5)

    def test_csv_reader_missing_file(self):
        """OPERATE & CHECK: Verify the CSV reader handles missing files gracefully."""
        # BUILD
        missing_file = "non_existent.csv"

        # OPERATE
        headers, data = Marker_convert_csv_unknow_report_to_csv(missing_file)

        # CHECK
        self.assertEqual(headers, [], "Headers should be empty for missing file")
        self.assertEqual(data, [], "Data should be empty for missing file")

if __name__ == '__main__':
    unittest.main()
