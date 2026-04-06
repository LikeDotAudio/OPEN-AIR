
import sys
import os
import pathlib
import unittest
import io

# Setup environment
project_root = pathlib.Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Entry import initialize_test_logging, TEST_LOGGER
test_log_dir = project_root / "oaDataLogs" / "TestLog"
path = initialize_test_logging(str(test_log_dir))
print(f"DEBUG: initialize_test_logging returned: {path}")

TEST_LOGGER.info("🧪 [DEBUG] This is a test log message from the debug script.")

def run_test_and_capture():
    print("🚀 Running test...")
    # ... minimal run
    TEST_LOGGER.success("✅ [DEBUG] Test completed successfully.")

if __name__ == "__main__":
    run_test_and_capture()
    import time
    print("Waiting 2 seconds for BatchLogSink to flush...")
    time.sleep(2)
