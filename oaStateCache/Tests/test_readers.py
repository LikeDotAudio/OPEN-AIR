# Tests/test_readers.py
#
# Basic test for file readers.
#
# Author: Anthony Peter Kuzub
# Version: 20260327.1500.1

import unittest
from pathlib import Path


class TestReaders(unittest.TestCase):
    def test_asset_exists(self):
        # BUILD
        asset_dir = Path(__file__).parent / 'Assets'
        # OPERATE
        exists = asset_dir.exists()
        # CHECK
        self.assertTrue(exists)

if __name__ == '__main__':
    unittest.main()
