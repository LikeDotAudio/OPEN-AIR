import os
from pathlib import Path
from datetime import datetime

REPORT_PATH = '/home/anthony/Documents/OPEN-AIR/oaDataAudits/Audit_Bad_Tests_20260327.md'
# Modules to audit
modules = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('oa') and not d.startswith('oaData') and d not in ['oaReports', 'oaDocumentation', 'oaTests']]

results = []

for mod in modules:
    mod_path = Path(mod)
    test_dir = mod_path / 'Tests'
    reader_dir = mod_path / 'FileReaders'
    
    has_test_dir = test_dir.exists()
    test_files = []
    if has_test_dir:
        test_files = list(test_dir.glob('test_*.py')) + list(test_dir.glob('*_tester.py'))
    
    readers = [f for f in reader_dir.glob('*.py') if f.name != '__init__.py'] if reader_dir.exists() else []
    
    sample_assets = []
    if has_test_dir:
        # Look for typical input files in the module tree or specifically in Tests
        sample_assets = [f for f in test_dir.rglob('*') if f.suffix.lower() in ['.csv', '.json', '.pdf', '.log', '.html', '.shw', '.txt', '.xml', '.ini'] and f.is_file()]

    poor_quality_tests = []
    for tf in test_files:
        try:
            content = tf.read_text()
            if 'assert' not in content and 'self.assert' not in content:
                poor_quality_tests.append(tf.name)
        except:
            pass

    results.append({
        'module': mod,
        'has_test_dir': has_test_dir,
        'test_count': len(test_files),
        'test_files': [f.name for f in test_files],
        'reader_count': len(readers),
        'sample_asset_count': len(sample_assets),
        'poor_quality_tests': poor_quality_tests
    })

# --- Generate Markdown ---
report = [f'# OPEN-AIR QA Audit: Unit Test Coverage & Integrity ({datetime.now().strftime("%Y-%m-%d")})']
report.append('\n## Executive Summary')

missing_tests = [r['module'] for r in results if r['test_count'] == 0]
missing_assets = [r['module'] for r in results if r['reader_count'] > 0 and r['sample_asset_count'] == 0]

report.append(f'- **Total Software Modules Audited**: {len(results)}')
report.append(f'- **Modules Missing Tests**: {len(missing_tests)}')
report.append(f'- **Modules Missing Sample Assets for Readers**: {len(missing_assets)}')
report.append(f'- **Status**: {"🛑 CRITICAL GAP" if missing_tests else "✅ COVERAGE HEALTHY"}')

report.append('\n## 🚨 Critical Violations: Modules with NO Tests')
report.append('| Module | Readers Found | Sample Assets |')
report.append('| :--- | :---: | :---: |')
for r in results:
    if r['test_count'] == 0:
        asset_status = "❌ Missing" if r['reader_count'] > 0 and r['sample_asset_count'] == 0 else "N/A"
        report.append(f'| {r["module"]} | {r["reader_count"]} | {asset_status} |')

report.append('\n## ⚠️ Structural Debt: Poor Quality Tests (No Assertions)')
report.append('| Module | Test File | Issue |')
report.append('| :--- | :--- | :--- |')
for r in results:
    for pq in r['poor_quality_tests']:
        report.append(f'| {r["module"]} | {pq} | Script contains zero assertions; acts as a runner only. |')

report.append('\n## 📦 Data Integrity: Missing Sample Files for Readers')
found_missing_asset_modules = False
for r in results:
    if r['reader_count'] > 0 and r['sample_asset_count'] == 0:
        report.append(f'- **{r["module"]}**: Has {r["reader_count"]} file readers but 0 sample files in `Tests/`.')
        found_missing_asset_modules = True
if not found_missing_asset_modules:
    report.append('✅ All file readers have corresponding sample data in their module structure.')

report.append('\n## Refactoring Roadmap: The "GOOD" Test Standard')
report.append('1. **Fix the Ghost Tests**: Every file in the "Poor Quality" list must have `assert` statements added to validate behavioral contracts.')
report.append('2. **The Blueprint Pattern**: Use the **BUILD-OPERATE-CHECK** pattern. Example for a Reader:')
report.append('   ```python')
report.append('   # BUILD: Locate sample file in Tests/Assets/')
report.append('   # OPERATE: Call reader.parse(sample_path)')
report.append('   # CHECK: assert len(result) > 0')
report.append('   ```')

with open(REPORT_PATH, 'w') as f:
    f.write("\n".join(report))
print(f"Report generated at {REPORT_PATH}")
