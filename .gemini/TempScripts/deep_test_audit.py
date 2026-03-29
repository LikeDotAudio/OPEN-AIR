# .gemini/TempScripts/deep_test_audit.py
#
# Deep audit of the OPEN-AIR testing infrastructure.
#
# Author: Gemini (Collaborator)
# Version: 20260327.1600.1

import os
from pathlib import Path
from datetime import datetime

REPORT_PATH = '/home/anthony/Documents/OPEN-AIR/oaDataAudits/Audit_Bad_Tests_20260327.md'
PROJECT_ROOT = '/home/anthony/Documents/OPEN-AIR'

def audit():
    os.chdir(PROJECT_ROOT)
    modules = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('oa') 
               and not d.startswith('oaData') and d not in ['oaReports', 'oaDocumentation', 'oaTests']]
    
    results = []

    for mod in modules:
        mod_path = Path(mod)
        managers_dir = mod_path / 'Managers'
        workers_dir = mod_path / 'Workers'
        readers_dir = mod_path / 'FileReaders'
        tests_dir = mod_path / 'Tests'
        
        # 1. Functional Inventory
        managers = [f.name for f in managers_dir.glob('*.py') if f.name != '__init__.py'] if managers_dir.exists() else []
        workers = [f.name for f in workers_dir.glob('*.py') if f.name != '__init__.py'] if workers_dir.exists() else []
        readers = [f.name for f in readers_dir.glob('*.py') if f.name != '__init__.py'] if readers_dir.exists() else []
        
        # 2. Test Coverage
        test_files = list(tests_dir.glob('test_*.py')) + list(tests_dir.glob('*_tester.py')) if tests_dir.exists() else []
        
        # 3. Assertion & Quality Check
        ghost_tests = []
        for tf in test_files:
            try:
                content = tf.read_text()
                if 'assert' not in content and 'self.assert' not in content:
                    ghost_tests.append(tf.name)
            except:
                pass
        
        # 4. Asset Check
        assets_dir = tests_dir / 'Assets'
        has_assets = any(assets_dir.iterdir()) if assets_dir.exists() else False

        results.append({
            'module': mod,
            'managers': managers,
            'workers': workers,
            'readers': readers,
            'test_count': len(test_files),
            'ghost_tests': ghost_tests,
            'has_assets': has_assets,
            'missing_folders': [f for f in ['Managers', 'Workers', 'Tests'] if not (mod_path / f).exists()]
        })

    # --- Build Report ---
    report = [f'# OPEN-AIR QA Audit: Bad Test Modules & Coverage Gaps ({datetime.now().strftime("%Y-%m-%d")})']
    
    report.append('\n## Executive Summary')
    untested_functional = [r['module'] for r in results if (r['managers'] or r['workers']) and r['test_count'] == 0]
    report.append(f'- **Functional Modules Audited**: {len(results)}')
    report.append(f'- **Untested Functional Modules**: {len(untested_functional)}')
    report.append(f'- **Ghost Tests Found**: {sum(len(r["ghost_tests"]) for r in results)}')
    report.append(f'- **Status**: {"🛑 CRITICAL DEBT" if untested_functional else "✅ ARCHITECTURALLY SOUND"}')

    report.append('\n## 🚨 Critical Offender: No Test Coverage')
    report.append('Modules with active Managers/Workers but zero test files.')
    report.append('| Module | Functional Files | Issue |')
    report.append('| :--- | :---: | :--- |')
    for r in results:
        if (r['managers'] or r['workers']) and r['test_count'] == 0:
            count = len(r['managers']) + len(r['workers'])
            report.append(f'| {r["module"]} | {count} | No verification logic for core functional units. |')

    report.append('\n## ⚠️ Ghost Tests (Violation of Assertion Mandate)')
    report.append('Test files that execute code but fail to validate results (Zero `assert` calls).')
    report.append('| Module | Test File | Recommendation |')
    report.append('| :--- | :--- | :--- |')
    for r in results:
        for gt in r['ghost_tests']:
            report.append(f'| {r["module"]} | {gt} | Implement BUILD-OPERATE-CHECK with assertions. |')

    report.append('\n## 📦 Missing Mock Assets for Readers')
    report.append('| Module | Reader Count | Status |')
    report.append('| :--- | :---: | :--- |')
    for r in results:
        if r['readers'] and not r['has_assets']:
            report.append(f'| {r["module"]} | {len(r["readers"])} | ❌ Missing `Tests/Assets/` for functional verification. |')

    report.append('\n## 🛠️ Refactoring Roadmap: "GOOD" Test Samples')
    report.append('### Example: Standard Manager Test')
    report.append('```python')
    report.append('# BUILD: Instantiate Manager with Mock Config')
    report.append('# OPERATE: Call core method')
    report.append('# CHECK: assert state == expected')
    report.append('```')

    with open(REPORT_PATH, 'w') as f:
        f.write('\n'.join(report))
    print(f'✅ Audit complete. Report: {REPORT_PATH}')

if __name__ == "__main__":
    audit()
