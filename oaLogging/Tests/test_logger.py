import unittest
import os
import time
import shutil
import tempfile
from oaLogging.logger import BatchLogSink, initialize_logging, get_logger

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test.log")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_batch_log_sink(self):
        """Test that BatchLogSink writes to file in batches or on interval."""
        sink = BatchLogSink(self.log_file, format_str="{message}", batch_size=5, interval=1)
        
        # Write 3 messages (less than batch size)
        sink.write("msg1\n")
        sink.write("msg2\n")
        sink.write("msg3\n")
        
        # Check file - should be empty as batch_size not reached and interval not passed
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                self.assertEqual(f.read(), "")

        # Write 2 more messages (total 5, reaching batch size)
        sink.write("msg4\n")
        sink.write("msg5\n")
        
        # Give a tiny bit of time for thread to write
        time.sleep(0.1)
        
        self.assertTrue(os.path.exists(self.log_file))
        with open(self.log_file, "r") as f:
            content = f.read()
            self.assertIn("msg1", content)
            self.assertIn("msg5", content)
            
        sink.stop()

    def test_get_logger(self):
        """Test that get_logger returns a bound logger."""
        # We can't easily check internal Loguru state, but we can verify it doesn't crash
        # and returns something that looks like a logger.
        log = get_logger("TEST_CAT")
        self.assertTrue(hasattr(log, "debug"))
        self.assertTrue(hasattr(log, "info"))

if __name__ == "__main__":
    unittest.main()
