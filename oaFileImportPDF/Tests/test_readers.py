# Tests/test_readers.py
#
# Verification test for the SoundBase PDF asset.
#
# Author: Anthony Peter Kuzub
# Version: 20260327.1530.1

import unittest
from pathlib import Path

class TestPDFReaderAsset(unittest.TestCase):
    def test_sample_pdf_exists(self):
        """CHECK: Ensure the real-world SoundBase PDF is present."""
        # BUILD
        asset_path = Path(__file__).parent / 'Assets' / 'SOUND_BASE_PDF_V1.pdf'
        # OPERATE
        exists = asset_path.exists()
        # CHECK
        self.assertTrue(exists, f"Missing critical asset: {asset_path}")

if __name__ == '__main__':
    unittest.main()
