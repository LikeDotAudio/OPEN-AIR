# oaStand_Alone_Utilities/Tests/test_realign_logs.py
#
# Tests for the log realigner utility.
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import shutil
import tempfile
import unittest
from pathlib import Path

from oaStand_Alone_Utilities.Methods.realign_logs import HAS_RUST, realign_logs


class TestLogRealigner(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
        self.logs_dir = self.test_dir / "logs"
        self.logs_dir.mkdir()
        self.output_log = self.test_dir / "merged.log"

        # Create some mock log files
        self.log_content_1 = [
            "1711880000.500 | INFO | SYS | PROG1 | func1 | [DEBUG] Message 2",
            "1711880000.100 | INFO | SYS | PROG1 | func1 | [DEBUG] Message 1",
        ]
        self.log_content_2 = [
            "1711880000.800 | INFO | SYS | PROG2 | func2 | [DEBUG] Message 4",
            "1711880000.600 | INFO | SYS | PROG2 | func2 | [DEBUG] Message 3",
        ]

        with open(self.logs_dir / "log1.log", 'w') as f:
            f.write("\n".join(self.log_content_1) + "\n")
        with open(self.logs_dir / "log2.log", 'w') as f:
            f.write("\n".join(self.log_content_2) + "\n")

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def test_python_realign_logs(self):
        """Test the log realigner (Python fallback if Rust is missing)."""
        # We can't easily force Python fallback if HAS_RUST is True without monkeypatching,
        # but realign_logs should work regardless.
        success = realign_logs(str(self.logs_dir), str(self.output_log))
        self.assertTrue(success)
        self.assertTrue(self.output_log.exists())

        with open(self.output_log) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        self.assertEqual(len(lines), 4)
        timestamps = [float(line.split(' | ')[0]) for line in lines]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_rust_realign_logs(self):
        """Test the high-performance Rust log realigner if available."""
        if not HAS_RUST:
            self.skipTest("Rust LogAligner not available.")

        success = realign_logs(str(self.logs_dir), str(self.output_log))
        self.assertTrue(success)
        self.assertTrue(self.output_log.exists())

        with open(self.output_log) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        self.assertEqual(len(lines), 4)
        timestamps = [float(line.split(' | ')[0]) for line in lines]
        self.assertEqual(timestamps, sorted(timestamps))

if __name__ == '__main__':
    unittest.main()
