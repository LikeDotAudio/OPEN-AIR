# oaFileImportHTML/Tests/test_readers.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Unit tests for the HTML file reader.

import unittest
import os
import pathlib
from oaFileImportHTML.FileReaders.from_ias_html import convert_ias_html_to_markers

class TestHTMLReader(unittest.TestCase):
    """
    Tests the HTML reader module.
    Follows the F.I.R.S.T principles and BUILD-OPERATE-CHECK pattern.
    """

    def setUp(self):
        """BUILD: Define paths for test assets."""
        self.test_dir = pathlib.Path(__file__).resolve().parent
        self.sample_file = self.test_dir / "Assets" / "sample.html"

    def test_html_reader_functional(self):
        """OPERATE & CHECK: Verify the HTML reader correctly processes a sample file."""
        # BUILD
        with open(self.sample_file, "r") as f:
            html_content = f.read()

        # OPERATE
        headers, data = convert_ias_html_to_markers(html_content)

        # CHECK
        self.assertTrue(len(headers) > 0, "Headers should be returned")
        self.assertTrue(len(data) >= 1, "Data should contain at least 1 row")
        
        # Verify row data mapping
        first_row = data[0]
        self.assertEqual(first_row["ZONE"], "TestZone")
        self.assertEqual(first_row["GROUP"], "TestGroup")
        self.assertEqual(first_row["FREQ_MHZ"], 500.5)

if __name__ == '__main__':
    unittest.main()
