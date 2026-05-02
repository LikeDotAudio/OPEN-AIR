# Tests/test_readers.py
#
# Verification test for the IAS HTML report asset.
#
# Author: Anthony Peter Kuzub
# Version: 20260327.1530.1

import unittest
from pathlib import Path


class TestHTMLReaderAsset(unittest.TestCase):
    def test_sample_html_exists(self):
        """CHECK: Ensure the real-world IAS report HTML is present."""
        # BUILD
        asset_path = Path(__file__).parent / 'Assets' / 'IAS_report.html'
        # OPERATE
        exists = asset_path.exists()
        # CHECK
        self.assertTrue(exists, f"Missing critical asset: {asset_path}")

if __name__ == '__main__':
    unittest.main()
