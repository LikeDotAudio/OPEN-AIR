# oaFileImportShow/Tests/test_readers.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Unit tests for FileReaders in oaFileImportShow.

import unittest
import os
from pathlib import Path
from oaFileImportShow.FileReaders.from_shure_wwb_shw import convert_shure_wwb_shw_to_markers

class TestFileReaders(unittest.TestCase):
    """
    Harden FileReaders for oaFileImportShow.
    """

    def setUp(self):
        """BUILD: Define the path to the mock sample file."""
        self.assets_dir = Path(__file__).parent / "Assets"
        self.sample_shw = self.assets_dir / "sample.shw"

    def test_shw_reader(self):
        """OPERATE & CHECK: Verify that the SHW reader correctly parses the mock file."""
        # Ensure the mock file exists
        self.assertTrue(self.sample_shw.exists(), f"Mock file {self.sample_shw} not found.")

        # Operate
        headers, marker_data = convert_shure_wwb_shw_to_markers(str(self.sample_shw))

        # Check
        self.assertEqual(len(marker_data), 1)
        self.assertEqual(marker_data[0]["ZONE"], "Zone1")
        self.assertEqual(marker_data[0]["GROUP"], "Group1")
        self.assertEqual(marker_data[0]["DEVICE"], "Shure - ULXD - Band1")
        self.assertEqual(marker_data[0]["NAME"], "Mic1")
        self.assertEqual(marker_data[0]["FREQ_MHZ"], 600.0)

if __name__ == "__main__":
    unittest.main()
