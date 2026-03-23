# Tests/installation_validator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Validates that the system components are correctly installed and reachable.

import shutil
import os
import subprocess

def test_python_environment():
    """Verify minimum Python dependencies are present."""
    try:
        import loguru
        import textual
        return True, "Python environment validated."
    except ImportError as e:
        return False, f"Missing Python dependency: {e}"

def test_mosquitto_reachable():
    """Verify Mosquitto is in PATH and runnable."""
    if shutil.which('mosquitto'):
        return True, "Mosquitto broker binary found."
    return False, "Mosquitto broker not found in system path."

def test_snmp_reachable():
    """Verify SNMP daemon is in PATH."""
    if shutil.which('snmpd'):
        return True, "SNMP daemon binary found."
    return False, "SNMP daemon not found in system path."

def test_desktop_entry():
    """Verify the .desktop file exists in the local applications directory."""
    target = os.path.expanduser('~/.local/share/applications/OPEN-AIR.desktop')
    if os.path.exists(target):
        return True, f"Desktop entry found at {target}"
    return False, "Desktop entry missing."

def run_all_tests(callback=None):
    """Executes all installation validation tests."""
    tests = [
        ("Python Env", test_python_environment),
        ("Mosquitto", test_mosquitto_reachable),
        ("SNMP", test_snmp_reachable),
        ("Desktop Icon", test_desktop_entry),
    ]
    
    results = []
    for name, func in tests:
        success, message = func()
        results.append((name, success, message))
        if callback:
            status = "✅" if success else "❌"
            callback(f"{status} {name}: {message}")
            
    return all(r[1] for r in results)
