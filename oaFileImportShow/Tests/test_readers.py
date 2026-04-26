# Tests/test_readers.py
#
# Verification test for the Shure WWB venue asset.
#
# Author: Anthony Peter Kuzub
# Version: 20260327.1530.1

import unittest
from pathlib import Path


class TestShowReaderAsset(unittest.TestCase):
    def test_sample_shw_exists(self):
        """CHECK: Ensure the real-world WWB venue file is present."""
        # BUILD
        asset_path = Path(__file__).parent / 'Assets' / 'WWB_venue.shw'
        # OPERATE
        exists = asset_path.exists()
        # CHECK
        self.assertTrue(exists, f"Missing critical asset: {asset_path}")

if __name__ == '__main__':
    unittest.main()
