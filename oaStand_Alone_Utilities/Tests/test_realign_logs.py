# oaStand_Alone_Utilities/Tests/test_realign_logs.py
#
# Tests for the log realigner utility (Python vs Rust).
#
# Author: Anthony Peter Kuzub
# Version: 20260331.1210.1

import unittest
import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from oaStand_Alone_Utilities.Methods.realign_logs import realign_logs

class TestLogRealigner(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
        self.logs_dir = self.test_dir / "logs"
        self.logs_dir.mkdir()
        self.output_py = self.test_dir / "merged_py.log"
        self.output_rs = self.test_dir / "merged_rs.log"
        
        # Determine paths
        self.project_root = Path(__file__).parent.parent.parent
        self.rust_bin = self.project_root / "oaStand_Alone_Utilities/Methods/oaLogAligner-rs/target/release/oalogaligner"
        
        # Create some mock log files
        # Format: timestamp | level | partition | process | function | message
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
        success = realign_logs(str(self.logs_dir), str(self.output_py))
        self.assertTrue(success)
        self.assertTrue(self.output_py.exists())
        
        with open(self.output_py, 'r') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 4)
        timestamps = [float(line.split(' | ')[0]) for line in lines]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_rust_realign_logs(self):
        if not self.rust_bin.exists():
            self.skipTest("Rust binary not found. Please compile it first.")
            
        result = subprocess.run(
            [str(self.rust_bin), "--dir", str(self.logs_dir), "--output", str(self.output_rs)],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(self.output_rs.exists())
        
        with open(self.output_rs, 'r') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 4)
        timestamps = [float(line.split(' | ')[0]) for line in lines]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_compare_python_vs_rust(self):
        if not self.rust_bin.exists():
            self.skipTest("Rust binary not found. Please compile it first.")
            
        # Run Python
        realign_logs(str(self.logs_dir), str(self.output_py))
        
        # Run Rust
        subprocess.run(
            [str(self.rust_bin), "--dir", str(self.logs_dir), "--output", str(self.output_rs)],
            check=True
        )
        
        # Compare byte-for-byte
        with open(self.output_py, 'rb') as f_py, open(self.output_rs, 'rb') as f_rs:
            self.assertEqual(f_py.read(), f_rs.read())

if __name__ == '__main__':
    unittest.main()
