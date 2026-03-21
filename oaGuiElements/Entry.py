import unittest
import os
import sys
from io import StringIO

"""
oaGuiElements/Entry.py - Manager for GUI Elements and their Tests
"""

class CustomTestResult(unittest.TestResult):
    """
    Custom TestResult to capture test outcomes in a structured format.
    """
    def __init__(self, stream=None, descriptions=True, verbosity=1, tb_locals=False):
        super().__init__(stream=stream, descriptions=descriptions, verbosity=verbosity, tb_locals=tb_locals)
        self.results = []
        self._stream = stream # Store stream to format exceptions

    def addSuccess(self, test):
        super().addSuccess(test)
        self.results.append({
            "test_name": f"{test.__module__}.{test._testMethodName}",
            "status": "SUCCESS",
            "message": None,
            "traceback": None,
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        exc_type, exc_value, exc_traceback = err
        self.results.append({
            "test_name": f"{test.__module__}.{test._testMethodName}",
            "status": "FAILURE",
            "message": str(exc_value),
            "traceback": "".join(self._stream.formatException(err)) if self._stream else None,
        })

    def addError(self, test, err):
        super().addError(test, err)
        exc_type, exc_value, exc_traceback = err
        self.results.append({
            "test_name": f"{test.__module__}.{test._testMethodName}",
            "status": "ERROR",
            "message": str(exc_value),
            "traceback": "".join(self._stream.formatException(err)) if self._stream else None,
        })
        
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.results.append({
            "test_name": f"{test.__module__}.{test._testMethodName}",
            "status": "SKIPPED",
            "message": reason,
            "traceback": None,
        })


class GuiTestRunner(unittest.TextTestRunner):
    """
    Custom TextTestRunner that uses CustomTestResult.
    """
    def __init__(self, stream=None, descriptions=True, verbosity=1,
                 failfast=False, buffer=False, resultclass=None,
                 warnings=None, *, tb_locals=False):
        
        if stream is None:
            stream = StringIO()
        
        # If resultclass is not provided, use our CustomTestResult
        if resultclass is None:
            resultclass = CustomTestResult
            
        super().__init__(stream=stream, descriptions=descriptions, verbosity=verbosity,
                         failfast=failfast, buffer=buffer, resultclass=resultclass,
                         warnings=warnings, tb_locals=tb_locals)
        self._result_instance = None # To hold the CustomTestResult instance

    def _makeResult(self):
        # This method is called by TextTestRunner.run() to create the result object.
        # We ensure our CustomTestResult is used.
        # Pass the stream to CustomTestResult so it can format exceptions.
        self._result_instance = self.resultclass(self.stream, self.descriptions, self.verbosity, self.tb_locals)
        return self._result_instance

    def get_results(self):
        # Returns the structured results collected by CustomTestResult
        if self._result_instance:
            return self._result_instance.results
        return []

    def get_result_object(self):
        # Returns the actual TestResult object instance
        return self._result_instance

class GuiElementEntry:
    """
    Entry point and manager for GUI elements and their associated tests.
    This class is designed to discover, run, and report on GUI element tests.
    """
    def __init__(self, base_path="/home/anthony/Documents/OPEN-AIR/oaGuiElements"):
        self.base_path = base_path
        self.tests_path = os.path.join(self.base_path, "Tests")

    def discover_and_run_gui_tests(self):
        """
        Discovers all GUI tests in the 'Tests' directory and runs them using unittest.
        Returns a structured dictionary of test results and a summary.
        """
        if not os.path.exists(self.tests_path):
            return {
                "status": "error",
                "message": f"Test path '{self.tests_path}' does not exist.",
                "results": [],
                "summary": {"total_run": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
            }

        original_sys_path = list(sys.path)
        if self.tests_path not in sys.path:
            sys.path.insert(0, self.tests_path)
        
        try:
            loader = unittest.TestLoader()
            # Discover tests. pattern='test_*.py' is standard.
            suite = loader.discover(start_dir=self.tests_path, pattern='test_*.py')
            
            output_stream = StringIO()
            
            # Instantiate our custom runner, specifying CustomTestResult
            runner = GuiTestRunner(stream=output_stream, verbosity=2, resultclass=CustomTestResult)
            
            # Run the test suite. runner.run() returns the TestResult object.
            test_result_obj = runner.run(suite) 
            
            # Get the collected structured results from our custom result object
            custom_collected_results = runner.get_results()

            # Calculate summary statistics using the TestResult object returned by run()
            total_run = test_result_obj.testsRun
            failed_count = len(test_result_obj.failures)
            error_count = len(test_result_obj.errors)
            skipped_count = len(test_result_obj.skipped)
            passed_count = total_run - failed_count - error_count - skipped_count

            return {
                "status": "completed",
                "results": custom_collected_results, 
                "summary": {
                    "total_run": total_run,
                    "passed": passed_count,
                    "failed": failed_count,
                    "errors": error_count,
                    "skipped": skipped_count
                },
                "raw_output": output_stream.getvalue()
            }
        except Exception as e:
            sys.path = original_sys_path # Restore path
            
            return {
                "status": "error",
                "message": f"An unexpected error occurred during test execution: {e}",
                "results": [],
                "summary": {"total_run": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
            }
        finally:
            sys.path = original_sys_path # Always restore path

# If this script is run directly, execute the tests
if __name__ == '__main__':
    print("Initializing GUI Element Test Runner...")
    entry_manager = GuiElementEntry()
    print(f"Discovering tests in: {entry_manager.tests_path}")
    
    results_data = entry_manager.discover_and_run_gui_tests()
    
    import json
    print("--- Test Execution Results ---")
    
    if results_data.get("status") == "completed":
        summary = results_data['summary']
        print(f"Total Tests Run: {summary['total_run']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Errors: {summary['errors']}")
        print(f"Skipped: {summary['skipped']}")
        
        if summary['failed'] > 0 or summary['errors'] > 0:
            print("--- Failing/Errored Tests ---")
            for result in results_data['results']:
                if result['status'] in ('FAILURE', 'ERROR'):
                    print(f"Test: {result['test_name']}")
                    print(f"Status: {result['status']}")
                    print(f"Message: {result['message']}")
                    if result['traceback']:
                        print(f"Traceback:{result['traceback']}")
        
    elif results_data.get("status") == "error":
        print(f"Error: {results_data.get('message', 'An unknown error occurred.')}")
    else:
        print("No results to display.")
