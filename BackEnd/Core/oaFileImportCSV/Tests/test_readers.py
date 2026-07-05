# ==========================================
# Header: test_readers.py
# Purpose: test_readers.py implementation.
# Description: Logic and implementation for test_readers.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

# Tests/test_readers.py
#
# Verification test for the Basic CSV venue asset.
#
# Author: Anthony Peter Kuzub
# Version: 20260327.1530.1

import unittest
from pathlib import Path


class TestCSVReaderAsset(unittest.TestCase):
    def test_sample_csv_exists(self):
        """CHECK: Ensure the real-world venue CSV is present."""
        # BUILD
        asset_path = Path(__file__).parent / 'Assets' / 'Basic_CSV_venue.csv'
        # OPERATE
        exists = asset_path.exists()
        # CHECK
        self.assertTrue(exists, f"Missing critical asset: {asset_path}")

if __name__ == '__main__':
    unittest.main()
