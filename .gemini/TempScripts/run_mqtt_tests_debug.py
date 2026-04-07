
import sys
import os
import io
import unittest
from unittest.mock import MagicMock

# Inject project root
project_root = "/home/anthony/Documents/OPEN-AIR"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock TEST_LOGGER before import
import oaLogging.Entry
oaLogging.Entry.TEST_LOGGER = MagicMock()

from oaTests.Workers.TestRunner.TestRunner import TestRunner, CrashInterceptingResult

class DebugCrashInterceptingResult(CrashInterceptingResult):
    def stopTest(self, test):
        captured_err = self._stderr_buffer.getvalue()
        if captured_err:
            if "Traceback" in captured_err or "Exception" in captured_err:
                print(f"🚨🚨🚨 FOUND CRASH in {test} 🚨🚨🚨")
                print(captured_err)
                print("-" * 40)
        super().stopTest(test)

def run_all_mqtt_tests():
    # Discover tests
    loader = unittest.TestLoader()
    suite = loader.discover("oaComProtocols.oaComMQTT/Tests", pattern="test_*.py")

    # Run with CrashInterceptingResult
    runner = TestRunner()
    result = DebugCrashInterceptingResult(runner)
    
    print(f"--- Running {suite.countTestCases()} tests ---")
    suite.run(result)
    print("--- Done ---")

if __name__ == '__main__':
    run_all_mqtt_tests()
