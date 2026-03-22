# Audit Tools/audit_bad_tests.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
import ast
import re

project_root = "."
output_file = os.path.join(project_root, "oaDataAudits/Documentation/Audits/Bad_Tests_Audit.md")

# Paths to scan
SCAN_DIRS = ["managers", "workers"]

# Patterns for test files
TEST_PATTERNS = [
    r"^test_.*\.py$",
    r".*_test\.py$",
    r".*_tester\.py$",
    r"^tester\.py$"
]

def is_test_file(filename):
    for pattern in TEST_PATTERNS:
        if re.match(pattern, filename):
            return True
    return False

def get_assertions_count(node):
    count = 0
    for child in ast.walk(node):
        if isinstance(child, ast.Assert):
            count += 1
        # Also count common unittest assertions
        elif isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute) and child.func.attr.startswith("assert"):
                count += 1
    return count

def analyze_test_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return {"error": str(e)}

    test_functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_") or node.name.startswith("test"):
                test_functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "assertions": get_assertions_count(node),
                    "length": getattr(node, "end_lineno", node.lineno) - node.lineno
                })
    
    return {
        "functions": test_functions,
        "total_assertions": sum(f["assertions"] for f in test_functions),
        "total_functions": len(test_functions)
    }

def find_test_for_file(filepath):
    dir_name = os.path.dirname(filepath)
    base_name = os.path.basename(filepath)
    name_no_ext = os.path.splitext(base_name)[0]
    
    # Possible test names
    candidates = [
        f"test_{base_name}",
        f"{name_no_ext}_test.py",
        f"{name_no_ext}_tester.py",
        "tester.py",
        "test.py"
    ]
    
    # Check current dir
    for cand in candidates:
        cand_path = os.path.join(dir_name, cand)
        if os.path.exists(cand_path):
            return cand_path
            
    # Check 'tests' or 'tester' subdirectory
    for sub in ["tests", "tester", "Testing"]:
        sub_dir = os.path.join(dir_name, sub)
        if os.path.exists(sub_dir) and os.path.isdir(sub_dir):
            for cand in candidates:
                cand_path = os.path.join(sub_dir, cand)
                if os.path.exists(cand_path):
                    return cand_path
                
    return None

results = {
    "missing": [],
    "bad_quality": [],
    "healthy": []
}

total_modules = 0

for scan_dir in SCAN_DIRS:
    scan_path = os.path.join(project_root, scan_dir)
    for root, dirs, files in os.walk(scan_path):
        if any(ignore in root for ignore in [".git", "__pycache__", "DATA"]):
            continue
        for file in files:
            if file.endswith(".py") and not file.startswith("__") and not is_test_file(file):
                total_modules += 1
                module_path = os.path.join(root, file)
                rel_module_path = os.path.relpath(module_path, project_root)
                
                test_path = find_test_for_file(module_path)
                if not test_path:
                    results["missing"].append(rel_module_path)
                else:
                    analysis = analyze_test_file(test_path)
                    rel_test_path = os.path.relpath(test_path, project_root)
                    
                    issues = []
                    if analysis.get("total_functions", 0) == 0:
                        issues.append("Test file exists but contains no test functions")
                    if analysis.get("total_assertions", 0) == 0 and analysis.get("total_functions", 0) > 0:
                        issues.append("Test functions exist but contain no assertions (not actually validating)")
                    
                    for func in analysis.get("functions", []):
                        if func["length"] > 40:
                            issues.append(f"Test function '{func['name']}' is too long ({func['length']} lines)")
                        if func["assertions"] > 10:
                            issues.append(f"Test function '{func['name']}' has too many assertions ({func['assertions']}) - likely testing multiple concepts")

                    if issues:
                        results["bad_quality"].append({
                            "module": rel_module_path,
                            "test": rel_test_path,
                            "issues": list(set(issues))
                        })
                    else:
                        results["healthy"].append(rel_module_path)

# Generate Report
with open(output_file, "w", encoding="utf-8") as f:
    f.write("# Bad Tests Audit Report\n\n")
    
    f.write("## Executive Summary\n")
    f.write(f"Total modules analyzed: {total_modules}\n")
    f.write(f"- **Missing Tests**: {len(results['missing'])}\n")
    f.write(f"- **Bad Quality Tests**: {len(results['bad_quality'])}\n")
    f.write(f"- **Healthy Tests**: {len(results['healthy'])}\n\n")
    
    coverage = (len(results['healthy']) + len(results['bad_quality'])) / total_modules * 100 if total_modules > 0 else 0
    f.write(f"**Test Coverage Rate**: {coverage:.2f}%\n\n")
    
    f.write("## Top Offenders (Missing Tests)\n")
    f.write("These modules have no identified test or tester file. High priority for new test creation.\n\n")
    # Limit to top 20 for readability
    for m in sorted(results["missing"])[:20]:
        f.write(f"- {m}\n")
    if len(results["missing"]) > 20:
        f.write(f"\n... and {len(results['missing']) - 20} more.\n")
        
    f.write("\n## Poor Quality Tests\n")
    f.write("These modules have tests, but they violate clean testing principles.\n\n")
    for r in results["bad_quality"][:20]:
        f.write(f"### {r['module']}\n")
        f.write(f"**Test File:** {r['test']}\n")
        f.write("**Issues:**\n")
        for issue in r["issues"]:
            f.write(f"- {issue}\n")
        f.write("\n")

print(f"Audit complete. Results written to {output_file}")
