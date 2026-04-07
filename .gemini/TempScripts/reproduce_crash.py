
import sys
import os
import io
import unittest

# Inject project root
project_root = "/home/anthony/Documents/OPEN-AIR"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from oaTests.Workers.TestRunner.TestRunner import TestRunner, CrashInterceptingResult

class DebugCrashInterceptingResult(CrashInterceptingResult):
    def stopTest(self, test):
        captured_err = self._stderr_buffer.getvalue()
        if captured_err:
            print(f"--- Captured stderr for {test} ---\n{captured_err}\n--- End captured stderr ---")
        super().stopTest(test)

def run_repro():
    # Setup test
    from oaComProtocols.oaComMQTT.Tests.test_mqtt_manager import TestMqttManager
    suite = unittest.TestSuite()
    suite.addTest(TestMqttManager('test_attempt_reconnect_failed_connection'))

    # Run with CrashInterceptingResult
    runner = TestRunner()
    result = DebugCrashInterceptingResult(runner)
    
    # We need to mock TEST_LOGGER to avoid initialization issues in this script
    from unittest.mock import MagicMock
    import oaLogging.Entry
    oaLogging.Entry.TEST_LOGGER = MagicMock()

    print("--- Running test: test_initialization ---")
    suite.run(result)
    print("--- Test complete ---")

    if result.failures:
        for test, err in result.failures:
            print(f"FAILURE in {test}: {err}")
            # If it's our intercepted error, it will say "Background crash detected in stderr"
    
    # Check what was captured in the last stopTest
    # Since we only ran one test, we can check the buffer if we had a way to access it,
    # but the result object doesn't store it after stopTest.
    # Let's modify CrashInterceptingResult slightly for debugging or just check stdout/stderr
    # because CrashInterceptingResult writes captured_err back to real stderr.

if __name__ == '__main__':
    run_repro()
