import os
import sys
import unittest
import time
import json
import xml.etree.ElementTree as ET
import webbrowser
from datetime import datetime

class UnifiedTestRunner:
    def __init__(self, html_report_path, json_report_path):
        self.html_report_path = html_report_path
        self.json_report_path = json_report_path
        self.test_results = []
        self.summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0
        }

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

            def addFailure(self, test, err):
                duration = time.time() - self.start_times.get(test, time.time())
                self.runner._record(test, "failed", message=str(err[1]), duration=duration)
                super().addFailure(test, err)

            def addError(self, test, err):
                duration = time.time() - self.start_times.get(test, time.time())
                self.runner._record(test, "error", message=str(err[1]), duration=duration)
                super().addError(test, err)

            def addSkip(self, test, reason):
                duration = time.time() - self.start_times.get(test, time.time())
                self.runner._record(test, "skipped", message=reason, duration=duration)
                super().addSkip(test, reason)

        result = ReportingResult(self)
        full_suite.run(result)
        self._generate_reports()

    def _record(self, test, status, message="", duration=0):
        self.summary["total"] += 1
        if status == "passed": self.summary["passed"] += 1
        elif status == "failed": self.summary["failed"] += 1
        elif status == "error": self.summary["errors"] += 1
        elif status == "skipped": self.summary["skipped"] += 1

        # ⚡ EXTRACTION: Get the docstring to use as "Goal & Achievement"
        description = getattr(test, "_testMethodDoc", "") or "No description provided."
        description = description.strip().replace("\n", "<br>")

        self.test_results.append({
            "classname": test.__class__.__name__,
            "name": str(test),
            "status": status,
            "message": message,
            "description": description,
            "duration": f"{duration:.4f}s"
        })

    def _generate_reports(self):
        # 1. JSON Report
        with open(self.json_report_path, "w") as f:
            json.dump({"summary": self.summary, "details": self.test_results}, f, indent=4)
        
        # 2. HTML Report
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>OPEN-AIR Unified Test Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f4f7f6; color: #333; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 15px; margin-top: 0; }}
        .summary-box {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .stat {{ flex: 1; padding: 20px; border-radius: 6px; text-align: center; color: white; font-weight: bold; font-size: 1.1em; }}
        .total {{ background: #34495e; }}
        .passed {{ background: #27ae60; }}
        .failed {{ background: #e74c3c; }}
        .errors {{ background: #f39c12; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: fixed; }}
        th, td {{ border: 1px solid #eee; padding: 15px; text-align: left; vertical-align: top; overflow: hidden; word-wrap: break-word; }}
        th {{ background-color: #fafafa; color: #666; font-weight: 600; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.05em; }}
        tr:nth-child(even) {{ background-color: #fcfcfc; }}
        tr:hover {{ background-color: #f8f9fa; }}
        .status-passed {{ color: #27ae60; font-weight: bold; }}
        .status-failed {{ color: #e74c3c; font-weight: bold; }}
        .status-error {{ color: #f39c12; font-weight: bold; }}
        .description {{ font-size: 0.9em; color: #555; line-height: 1.4; }}
        .test-name {{ font-family: 'Courier New', Courier, monospace; font-size: 0.85em; color: #2980b9; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OPEN-AIR Unified Test Report</h1>
        <p style="color: #999; margin-bottom: 25px;">Generated on: <strong>{timestamp}</strong></p>
        
        <div class="summary-box">
            <div class="stat total">Total: {total}</div>
            <div class="stat passed">Passed: {passed}</div>
            <div class="stat failed">Failed: {failed}</div>
            <div class="stat errors">Errors: {errors}</div>
        </div>

        <table>
            <colgroup>
                <col style="width: 25%;">
                <col style="width: 50%;">
                <col style="width: 12%;">
                <col style="width: 13%;">
            </colgroup>
            <thead>
                <tr>
                    <th>Test Case</th>
                    <th>Goal & Achievement</th>
                    <th>Status</th>
                    <th>Duration</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        table_rows = []
        for r in self.test_results:
            row = f"""
                <tr>
                    <td class="test-name">{r['name']}</td>
                    <td class="description">{r['description']}</td>
                    <td class="status-{r['status']}">{r['status'].capitalize()}</td>
                    <td>{r['duration']}</td>
                </tr>
            """
            table_rows.append(row)

        html_content = html_template.format(
            timestamp=self.summary["timestamp"],
            total=self.summary["total"],
            passed=self.summary["passed"],
            failed=self.summary["failed"],
            errors=self.summary["errors"],
            table_rows="".join(table_rows)
        )
        
        with open(self.html_report_path, "w") as f:
            f.write(html_content)
        
        print(f"\n✅ Reports generated:")
        print(f"   - JSON: {self.json_report_path}")
        print(f"   - HTML: {self.html_report_path}")

def main():
    project_root = os.getcwd()
    sys.path.insert(0, project_root)
    
    # ⚡ DATA RELOCATION: Reports now kept in assets/DATA
    data_dir = os.path.join(project_root, 'assets', 'DATA', 'Testing')
    os.makedirs(data_dir, exist_ok=True)
    
    html_path = os.path.join(data_dir, 'test_execution_report.html')
    json_path = os.path.join(data_dir, 'test_results_report.json')
    
    runner = UnifiedTestRunner(html_path, json_path)
    runner.run([
        os.path.join(project_root, 'tests')
    ], top_level_dir=project_root)

    # 🌐 AUTO-OPEN: Open the report in the default browser
    print(f"🌐 Launching report...")
    webbrowser.open('file://' + os.path.realpath(html_path))

if __name__ == "__main__":
    main()
