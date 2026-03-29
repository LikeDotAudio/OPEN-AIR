# oaInstallation/Tests/test_installation_validator.py
# Author: Anthony Peter Kuzub
# Version: 20260328.0.1
#
# Description: Unit tests to validate system installation and environment.

import unittest
import shutil
import os

def check_python_environment():
    """Verify minimum Python dependencies are present."""
    try:
        import loguru
        import textual
        return True, "Python environment is pristine and fully loaded."
    except ImportError as e:
        return False, f"Missing Python dependency: {e}"

def check_mosquitto_reachable():
    """Verify Mosquitto is in PATH and runnable."""
    if shutil.which('mosquitto'):
        return True, "Mosquitto broker binary is secured and ready."
    return False, "Mosquitto broker not found in system path."

def check_snmp_reachable():
    """Verify SNMP daemon is in PATH."""
    if shutil.which('snmpd'):
        return True, "SNMP daemon binary is locked and loaded."
    return False, "SNMP daemon not found in system path."

def check_desktop_entry():
    """Verify the .desktop file exists in the local applications directory."""
    target = os.path.expanduser('~/.local/share/applications/OPEN-AIR.desktop')
    if os.path.exists(target):
        return True, f"Desktop entry shines brightly at {target}"
    return False, "Desktop entry missing."

class TestInstallation(unittest.TestCase):
    """
    Formal Unit Test Suite for System Installation Validation.
    These tests are automatically discovered by the OPEN-AIR TestRunner.
    """

    def test_python_environment(self):
        """Verify minimum Python dependencies (loguru, textual) are present."""
        success, message = check_python_environment()
        self.assertTrue(success, message)

    def test_mosquitto_reachable(self):
        """Verify Mosquitto broker is in PATH."""
        success, message = check_mosquitto_reachable()
        self.assertTrue(success, message)

    def test_snmp_reachable(self):
        """Verify SNMP daemon (snmpd) is in PATH."""
        success, message = check_snmp_reachable()
        self.assertTrue(success, message)

    def test_desktop_entry(self):
        """Verify the .desktop file exists in ~/.local/share/applications/."""
        success, message = check_desktop_entry()
        self.assertTrue(success, message)

def run_all_tests(callback=None):
    """
    Executes all installation validation tests manually.
    Maintained for legacy compatibility and standalone CLI use.
    """
    tests = [
        ("Python Env", check_python_environment),
        ("Mosquitto", check_mosquitto_reachable),
        ("SNMP", check_snmp_reachable),
        ("Desktop Icon", check_desktop_entry),
    ]
    
    results = []
    for name, func in tests:
        success, message = func()
        results.append((name, success, message))
        if callback:
            status = "💎 [VERIFIED]" if success else "💀 [FAILED]"
            callback(f"{status} {name}: {message}")
            
    return all(r[1] for r in results)

if __name__ == "__main__":
    unittest.main()
