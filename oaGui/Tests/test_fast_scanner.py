# oaGui/Tests/test_folder_fast_io_utility.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for folder_fast_io_utility.py

import pathlib
import shutil
import tempfile
import unittest

from oaGui.FileReaders.scanner.folder_fast_io_utility import FastScanner


class TestFastScanner(unittest.TestCase):
    """Verifies that the directory scanner works correctly, including fallback logic."""

    def setUp(self):
        """Build a temporary directory tree for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = pathlib.Path(self.test_dir)

        # Create some files and directories
        (self.test_path / "subdir1").mkdir()
        (self.test_path / "subdir2").mkdir()
        (self.test_path / "subdir1" / "file1.py").touch()
        (self.test_path / "subdir1" / "file2.txt").touch()
        (self.test_path / "subdir2" / "file3.py").touch()
        (self.test_path / "root_file.py").touch()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_scan_python_files(self):
        """OPERATE: Scan for .py files. CHECK: Verify all matching files are found."""
        scanner = FastScanner()
        results = scanner.scan_directory(self.test_dir, ".py")

        # Should find: subdir1/file1.py, subdir2/file3.py, root_file.py
        self.assertEqual(len(results), 3)
        self.assertTrue(any(res.endswith("file1.py") for res in results))
        self.assertTrue(any(res.endswith("file3.py") for res in results))
        self.assertTrue(any(res.endswith("root_file.py") for res in results))

    def test_scan_all_files(self):
        """OPERATE: Scan for all files. CHECK: Verify every file is identified."""
        scanner = FastScanner()
        results = scanner.scan_directory(self.test_dir)

        # Should find 4 files total
        self.assertEqual(len(results), 4)

    def test_invalid_path(self):
        """OPERATE: Scan a non-existent directory. CHECK: Verify it handles errors gracefully."""
        scanner = FastScanner()
        results = scanner.scan_directory("/tmp/this_path_should_never_exist_20260404")
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
