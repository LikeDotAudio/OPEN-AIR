import os
import glob
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

def find_test_files(test_dir='tests'):
    """Finds all Python test files (convention: test_*.py) in the specified directory and its subdirectories."""
    test_files = glob.glob(os.path.join(test_dir, '**', 'test_*.py'), recursive=True)
    return test_files

def run_tests(test_files, junit_report_path='report.xml'):
    """Runs pytest on the discovered test files and generates a JUnit XML report."""
    if not test_files:
        print("No test files found. Exiting.")
        return False

    # Construct the pytest command.
    # --junitxml generates the report, --durations=0 shows test durations.
    # Using shell=True might be necessary if pytest is not directly in PATH,
    # but it's generally safer to avoid if possible. For simplicity here, assume pytest is in PATH.
    # We'll run pytest in the project root to ensure correct module discovery.
    command = [
        'pytest',
        f'--junitxml={junit_report_path}',
        '--durations=0',
    ]
    command.extend(test_files)

    print(f"Running command: {' '.join(command)}")

    try:
        # Execute pytest. capture_output=True to get stdout/stderr.
        # text=True decodes stdout/stderr as strings.
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        print(f"Pytest stdout:{result.stdout}")
        print(f"Pytest stderr:{result.stderr}")
        if result.returncode != 0 and result.returncode != 1: # 0=passed, 1=failed, 2=error
            print(f"Pytest execution failed with return code {result.returncode}")
            return False
        return True
    except FileNotFoundError:
        print("Error: 'pytest' command not found. Please ensure pytest is installed and in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during test execution: {e}")
        return False

def parse_junit_xml_report(junit_report_path):
    """Parses the JUnit XML report to extract test results."""
    test_results = []
    try:
        tree = ET.parse(junit_report_path)
        root = tree.getroot()
        for testsuite in root.findall('testsuite'):
            for testcase in testsuite.findall('testcase'):
                name = testcase.get('name')
                classname = testcase.get('classname')
                duration = float(testcase.get('time', 0))
                
                status = 'passed'
                if testcase.find('failure') is not None:
                    status = 'failed'
                elif testcase.find('skipped') is not None:
                    status = 'skipped'
                
                test_results.append({
                    'classname': classname,
                    'name': name,
                    'status': status,
                    'duration': f"{duration:.4f}s"
                })
        return test_results
    except ET.ParseError:
        print(f"Error parsing JUnit XML report: {junit_report_path}")
        return None
    except FileNotFoundError:
        print(f"JUnit XML report not found: {junit_report_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during report parsing: {e}")
        return None

def generate_html_report(test_results, output_path='test_report.html'):
    """Generates a simple HTML report from the parsed test results."""
    if test_results is None:
        print("No test results to generate HTML report.")
        return

    # Basic HTML template
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .passed {{ color: green; font-weight: bold; }}
        .failed {{ color: red; font-weight: bold; }}
        .skipped {{ color: orange; }}
        .summary {{ margin-top: 20px; font-style: italic; }}
    </style>
</head>
<body>
    <h1>Test Execution Report</h1>
    <p class="summary">Generated on: {generation_time}</p>
    <p class="summary">Total Tests Found: {total_tests}</p>
    <p class="summary">Passed: {passed_tests}</p>
    <p class="summary">Failed: {failed_tests}</p>
    <p class="summary">Skipped: {skipped_tests}</p>

    <table>
        <thead>
            <tr>
                <th>Class Name</th>
                <th>Test Name</th>
                <th>Status</th>
                <th>Duration</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</body>
</html>
"""

    table_rows = []
    passed_count = 0
    failed_count = 0
    skipped_count = 0

    for result in test_results:
        status_class = result['status']
        if status_class == 'passed':
            passed_count += 1
        elif status_class == 'failed':
            failed_count += 1
        elif status_class == 'skipped':
            skipped_count += 1
            
        table_rows.append(f"""
            <tr>
                <td>{result['classname']}</td>
                <td>{result['name']}</td>
                <td class="{status_class}">{result['status'].capitalize()}</td>
                <td>{result['duration']}</td>
            </tr>
        """)

    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_tests = len(test_results)

    html_content = html_template.format(
        generation_time=generation_time,
        total_tests=total_tests,
        passed_tests=passed_count,
        failed_tests=failed_count,
        skipped_tests=skipped_count,
        table_rows="".join(table_rows)
    )

    try:
        with open(output_path, 'w') as f:
            f.write(html_content)
        print(f"HTML report generated successfully at: {output_path}")
    except IOError as e:
        print(f"Error writing HTML report to {output_path}: {e}")

def main():
    project_root = os.getcwd() # Assuming the script is run from the project root
    test_discovery_dir = os.path.join(project_root, 'tests') # Default test directory
    junit_report_path = os.path.join(project_root, 'report.xml') # Temporary JUnit report
    html_report_path = os.path.join(project_root, 'assets', 'Documentation', 'Testing', 'test_execution_report.html')

    # Ensure the output directory for HTML report exists
    os.makedirs(os.path.dirname(html_report_path), exist_ok=True)

    print(f"Discovering test files in: {test_discovery_dir}")
    test_files = find_test_files(test_discovery_dir)

    if run_tests(test_files, junit_report_path):
        print(f"Parsing JUnit XML report: {junit_report_path}")
        test_results = parse_junit_xml_report(junit_report_path)
        if test_results:
            generate_html_report(test_results, html_report_path)
        else:
            print("Failed to parse test results.")
    else:
        print("Test execution encountered errors or no tests were found/run.")
        # Optionally, create a minimal report indicating failure to run tests
        generate_html_report(None, html_report_path) # Pass None to indicate no results

    # Clean up the temporary JUnit XML report
    if os.path.exists(junit_report_path):
        try:
            os.remove(junit_report_path)
            print(f"Cleaned up temporary report: {junit_report_path}")
        except OSError as e:
            print(f"Error removing temporary report {junit_report_path}: {e}")

if __name__ == "__main__":
    main()
