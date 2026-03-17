import unittest
import os
import sys
import time
import json
from datetime import datetime

class TestReportGenerator:
    def __init__(self, report_path="test_results_report.json"):
        self.report_path = report_path
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "details": []
        }

    def add_result(self, test_name, status, message="", duration=0):
        self.results["total"] += 1
        if status == "PASS":
            self.results["passed"] += 1
        elif status == "FAIL":
            self.results["failed"] += 1
        else:
            self.results["errors"] += 1
        
        self.results["details"].append({
            "name": test_name,
            "status": status,
            "message": message,
            "duration": f"{duration:.4f}s"
        })

    def save(self):
        with open(self.report_path, "w") as f:
            json.dump(self.results, f, indent=4)
        print(f"\nReport saved to {self.report_path}")
        
        # Also print a nice summary
        print("-" * 30)
        print(f"Test Summary ({self.results['timestamp']})")
        print(f"Total:  {self.results['total']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Errors: {self.results['errors']}")
        print("-" * 30)

def run_tests():
    report = TestReportGenerator()
    loader = unittest.TestLoader()
    # Find all test_*.py files in the current directory
    suite = loader.discover(start_dir="assets/Documentation/Testing", pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    
    # We want to intercept the results to add them to our report
    class ReportingResult(unittest.TestResult):
        def __init__(self, report):
            super().__init__()
            self.report = report
            self.start_times = {}

        def startTest(self, test):
            self.start_times[test] = time.time()
            super().startTest(test)

        def addSuccess(self, test):
            duration = time.time() - self.start_times.get(test, time.time())
            self.report.add_result(str(test), "PASS", duration=duration)
            super().addSuccess(test)

        def addFailure(self, test, err):
            duration = time.time() - self.start_times.get(test, time.time())
            self.report.add_result(str(test), "FAIL", message=str(err[1]), duration=duration)
            super().addFailure(test, err)

        def addError(self, test, err):
            duration = time.time() - self.start_times.get(test, time.time())
            self.report.add_result(str(test), "ERROR", message=str(err[1]), duration=duration)
            super().addError(test, err)

    result = ReportingResult(report)
    suite.run(result)
    report.save()

if __name__ == "__main__":
    # Ensure project root is in path
    sys.path.insert(0, os.getcwd())
    run_tests()
