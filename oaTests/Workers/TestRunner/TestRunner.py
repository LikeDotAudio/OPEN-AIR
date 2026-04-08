# oaTests/Workers/TestRunner/TestRunner.py
# Author: Anthony Peter Kuzub
# Version: 1.3.0
#
# Description: Custom TestRunner and Result collector for OPEN-AIR.
# Intercepts stderr to detect and fail on background crashes (e.g. Tkinter callbacks).

import os
import time
import unittest
import sys
import io
from datetime import datetime
from oaLogging.Entry import TEST_LOGGER

class CrashInterceptingResult(unittest.TestResult):
    """
    A TestResult that captures stderr and fails the test if a traceback or 
    background exception is detected during execution.
    """
    def __init__(self, runner):
        super().__init__()
        self.runner = runner
        self.start_times = {}
        self._stderr_buffer = None
        self._original_stderr = None

    def startTest(self, test):
        self.start_times[test] = time.time()
        # Intercept stderr
        self._original_stderr = sys.stderr
        self._stderr_buffer = io.StringIO()
        sys.stderr = self._stderr_buffer
        super().startTest(test)

    def stopTest(self, test):
        # Restore stderr
        captured_err = self._stderr_buffer.getvalue()
        sys.stderr = self._original_stderr
        
        # Write captured output back to real stderr so it's still visible
        if captured_err:
            sys.stderr.write(captured_err)
        super().stopTest(test)

    def addSuccess(self, test):
        duration = time.time() - self.start_times.get(test, time.time())
        self.runner._record(test, "passed", duration=duration)
        super().addSuccess(test)

    def _get_failure_cause(self, err):
        import traceback
        try:
            exctype, value, tb = err
            if tb:
                tblist = traceback.extract_tb(tb)
                # Filter out unittest internal frames for cleaner reporting
                relevant_frames = [f for f in tblist if "unittest/case.py" not in f.filename]
                if not relevant_frames and tblist:
                    relevant_frames = tblist
                
                if relevant_frames:
                    filename, line, func, text = relevant_frames[-1]
                    # Using \n for breaks, let CSS white-space: pre-wrap or markdown handle it
                    return f"{value}\nAt {os.path.basename(filename)}:{line} in {func} -> {text}"
            return str(value)
        except:
            return "Unknown Failure Cause"

    def addFailure(self, test, err):
        duration = time.time() - self.start_times.get(test, time.time())
        cause = self._get_failure_cause(err)
        self.runner._record(test, "failed", message=str(err[1]), cause=cause, duration=duration)
        super().addFailure(test, err)

    def addError(self, test, err):
        duration = time.time() - self.start_times.get(test, time.time())
        cause = self._get_failure_cause(err)
        self.runner._record(test, "error", message=str(err[1]), cause=cause, duration=duration)
        super().addError(test, err)

    def addSkip(self, test, reason):
        duration = time.time() - self.start_times.get(test, time.time())
        self.runner._record(test, "skipped", message=reason, duration=duration)
        super().addSkip(test, reason)

class TestRunner:
    def __init__(self, record_callback=None):
        """
        Initializes the TestRunner.
        Args:
            record_callback: Optional function(test, status, message, cause, duration) 
                             to handle result reporting. If None, prints to console.
        """
        self.record_callback = record_callback

    def run(self, search_dirs, top_level_dir=None):
        loader = unittest.TestLoader()
        suites = []
        for d in search_dirs:
            if os.path.exists(d):
                try:
                    suites.append(loader.discover(d, pattern="test_*.py", top_level_dir=top_level_dir))
                except ImportError as e:
                    TEST_LOGGER.error(f"❌ ImportError in {d}: {e}")
                    if not self.record_callback:
                        print(f"❌ ImportError in {d}: {e}")
        
        full_suite = unittest.TestSuite(suites)
        result = CrashInterceptingResult(self)
        full_suite.run(result)
        return result

    def _record(self, test, status, message="", cause="", duration=0):
        # Pass the record up to the provided callback
        if self.record_callback:
            self.record_callback(test, status, message, cause, duration)
        
        # Always log to the specialized TEST_LOGGER (TestLog directory)
        emoji = "✅" if status == "passed" else "❌"
        if status == "passed":
            TEST_LOGGER.success(f"{emoji} {test}: {status} ({duration:.4f}s)")
        elif status == "skipped":
            TEST_LOGGER.warning(f"⏭️ {test}: {status} - {message}")
        else:
            TEST_LOGGER.error(f"{emoji} {test}: {status} ({duration:.4f}s)")
            if message:
                TEST_LOGGER.error(f"   [MSG] {message}")
            if cause:
                # Remove HTML tags for log readability
                clean_cause = cause.replace("<br>", "\n").replace("<small><i>", "").replace("</i></small>", "")
                TEST_LOGGER.error(f"   [CAUSE] {clean_cause}")

        # Fallback console print if no callback is active
        if not self.record_callback:
            print(f"{emoji} {test}: {status} ({duration:.4f}s)")
            if message:
                print(f"   [MSG] {message}")
