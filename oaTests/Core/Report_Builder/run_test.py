import os
import time
import unittest
from datetime import datetime

class ReportingResult(unittest.TestResult):
    def __init__(self, runner):
        super().__init__()
        self.runner = runner
        self.start_times = {}

    def startTest(self, test):
        self.start_times[test] = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        duration = time.time() - self.start_times.get(test, time.time())
        self.runner._record(test, "passed", duration=duration)
        super().addSuccess(test)

    def _get_failure_cause(self, err):
        import traceback
        exctype, value, tb = err
        # Get the last entry in the traceback (where it actually failed)
        tblist = traceback.extract_tb(tb)
        if tblist:
            filename, line, func, text = tblist[-1]
            return f"{value}<br><small><i>At {os.path.basename(filename)}:{line} in {func} -> {text}</i></small>"
        return str(value)

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
    def __init__(self, record_callback):
        self.record_callback = record_callback

    def run(self, search_dirs, top_level_dir=None):
        loader = unittest.TestLoader()
        suites = []
        for d in search_dirs:
            if os.path.exists(d):
                print(f"🔍 Discovering tests in: {d}")
                try:
                    suites.append(loader.discover(d, pattern="test_*.py", top_level_dir=top_level_dir))
                except ImportError as e:
                    print(f"❌ ImportError in {d}: {e}")
        
        full_suite = unittest.TestSuite(suites)
        result = ReportingResult(self)
        full_suite.run(result)
        return result

    def _record(self, test, status, message="", cause="", duration=0):
        # Pass the record up to the entry orchestrator
        self.record_callback(test, status, message, cause, duration)
