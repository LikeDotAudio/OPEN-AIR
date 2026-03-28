# oaFileImportPDF/Tests/test_readers.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Unit tests for the PDF file reader.

import unittest
from unittest.mock import MagicMock, patch
import os
import pathlib
import numpy as np
from oaFileImportPDF.FileReaders.from_soundbase_pdf_v1 import convert_soundbase_pdf_v1_to_markers

class TestPDFReader(unittest.TestCase):
    """
    Tests the PDF reader module.
    Follows the F.I.R.S.T principles and BUILD-OPERATE-CHECK pattern.
    """

    def setUp(self):
        """BUILD: Define paths for test assets."""
        self.test_dir = pathlib.Path(__file__).resolve().parent
        self.sample_file = self.test_dir / "Assets" / "sample.pdf"

    @patch('pdfplumber.open')
    def test_pdf_reader_functional(self, mock_pdf_open):
        """OPERATE & CHECK: Verify the PDF reader correctly processes a mocked PDF structure."""
        # BUILD: Mock the PDF structure
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        mock_page.extract_text.return_value = "Test Group (10 frequencies)\nModel Frequency"
        # Mock table structure: model, band, name, preset, spacing, frequency
        mock_page.extract_tables.return_value = [
            [["ModelX", "BandA", "NameA", "Preset1", "25k", "500.5"]]
        ]

        # OPERATE
        headers, data = convert_soundbase_pdf_v1_to_markers(str(self.sample_file))

        # CHECK
        self.assertTrue(len(headers) > 0, "Headers should be returned")
        self.assertTrue(len(data) >= 1, "Data should contain at least 1 row")
        
        # Verify row data mapping
        first_row = data[0]
        self.assertEqual(first_row["ZONE"], "Test Group (10 frequencies)")
        self.assertEqual(first_row["GROUP"], "ModelX")
        self.assertEqual(first_row["FREQ_MHZ"], 500.5)

if __name__ == '__main__':
    unittest.main()
