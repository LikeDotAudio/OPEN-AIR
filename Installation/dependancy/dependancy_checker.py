# Installation/dependancy/dependancy_checker.py
#
# Automated validation and repair of Python library requirements.
#

"""
Primary Purpose:
This module manages the identification, verification, and automated installation
 of third-party Python packages required for the OPEN-AIR platform.
"""

import os
import sys
import subprocess

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger

# --- Constants ---
VERSION = "20260314.004000.REV01"
EXIT_CODE_DEPENDENCY_FAILURE = 1

# EXTERNAL_PACKAGES: Maps human-friendly names to actual Python import paths.
EXTERNAL_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "Pillow (for Matplotlib/Tkinter image support)": "PIL",
    "pdfplumber": "pdfplumber",
    "beautifulsoup4 (bs4)": "bs4",
    "pyvisa": "pyvisa",
    "pyusb": "usb.core",
    "python-usbtmc": "usbtmc",
    "python-vxi11": "vxi11",
    "pyserial": "serial",
    "psutil": "psutil",
    "zeroconf": "zeroconf",
    "scapy": "scapy",
    "paho-mqtt": "paho.mqtt.client",
    "aiomqtt": "aiomqtt",
    "orjson": "orjson",
    "flameprof": "flameprof",
    "loguru": "loguru",
    "python-osc": "pythonosc",
    "mido": "mido",
    "python-rtmidi": "rtmidi",
}

# BUILTIN_PACKAGES: Standard library modules verified for baseline environment.
BUILTIN_PACKAGES = {
    "python-csv": "csv",
    "python-threading": "threading",
    "python-subprocess": "subprocess",
    "python-pathlib": "pathlib",
    "python-json": "json",
}

ACTION_INSTALL = "install"
ACTION_UNINSTALL = "uninstall"
FLAG_BREAK_SYSTEM_PACKAGES = "--break-system-packages"
FLAG_ASSUME_YES = "-y"
ERROR_NOT_INSTALLED = "not installed"
CRITICAL_FAILURE_MESSAGE = "❌ CRITICAL FAILURE: Missing/Failed Dependencies!"
MANUAL_INSTALL_INSTRUCTION = (
    "\nManual installation may be required. Remember to use a virtual "
    "environment or the '--break-system-packages' flag."
)

def _execute_pip_command(action, package_name, console_print_func, 
                         debug_log_func):
    """
    Invokes the 'pip' module to perform a specific package action.
    """
    # Use current interpreter to avoid 'pip' version or path mismatches.
    command = [sys.executable, "-m", "pip", action, package_name, 
               FLAG_BREAK_SYSTEM_PACKAGES]
    if action == ACTION_UNINSTALL:
        command.append(FLAG_ASSUME_YES)

    try:
        # Check=False allows us to handle non-zero exits via status code.
        result = subprocess.run(command, capture_output=True, text=True, 
                                check=False)
        if result.returncode == 0:
            if LOCAL_DEBUG:
                logger.success(f"✅✅✅ [SUCCESS] Pip {action} successful "
                               f"for {package_name}.")
            return True
        else:
            if action == ACTION_UNINSTALL:
                stderr_lower = result.stderr.lower()
                # Treat 'already uninstalled' as a success to avoid false errors.
                if (ERROR_NOT_INSTALLED in stderr_lower or 
                    "permission denied" in stderr_lower):
                    return True 
            # Gravity of Errors: Critical reporting if the repair fails.
            logger.error(f"🔍📦🔗 [DEPENDENCY] ERROR: Pip {action} failed "
                         f"for {package_name}: {result.stderr.strip()}")
            return False
    except Exception:
        # Capture forensic details for unexpected OS-level failures.
        logger.exception(f"🔍📦🔗 [DEPENDENCY] CRITICAL: Unexpected error "
                         f"during pip {action} for {package_name}.")
        return False

def action_check_dependancies(console_print_func, debug_log_func, 
                              should_clean_install=False):
    """
    Iterates through all required packages and verifies their availability.
    """
    missing_packages = []
    if LOCAL_DEBUG:
        logger.info(f"🔍📦🔗 [DEPENDENCY] Checking dependencies. "
                    f"Clean Mode: {should_clean_install}")

    for friendly_name, import_name in EXTERNAL_PACKAGES.items():
        # Derive the PyPI package name from the import name unless overridden.
        package_name_for_pip = import_name.split(".")[0]
        
        # --- Package Name Overrides ---
        # Some libraries have import names that differ from their PyPI name.
        if friendly_name == "paho-mqtt": package_name_for_pip = "paho-mqtt"
        elif friendly_name == "python-usbtmc": 
            package_name_for_pip = "python-usbtmc"
        elif friendly_name == "python-vxi11": 
            package_name_for_pip = "python-vxi11"
        elif friendly_name == "pyserial": 
            package_name_for_pip = "pyserial"
        elif friendly_name == "beautifulsoup4 (bs4)": 
            package_name_for_pip = "beautifulsoup4"
        elif friendly_name == "Pillow (for support)": 
            package_name_for_pip = "Pillow"
        elif friendly_name == "python-osc": 
            package_name_for_pip = "python-osc"
        elif friendly_name == "python-rtmidi": 
            package_name_for_pip = "python-rtmidi"

        try:
            # Use __import__ for light verification without complex namespace side effects.
            module = __import__(import_name)
            is_installed = True
            
            # Implementation Note: rtmidi has a common name collision.
            # 'python-rtmidi' contains 'MidiIn', while the bare 'rtmidi' does not.
            if import_name == "rtmidi":
                if not hasattr(module, "MidiIn"):
                    is_installed = False
                    if LOCAL_DEBUG:
                        logger.warning("🔍📦🔗 [DEPENDENCY] WARNING: "
                                       "Need 'python-rtmidi' (collision).")
        except ImportError:
            is_installed = False

        if is_installed and should_clean_install:
            _execute_pip_command(ACTION_UNINSTALL, package_name_for_pip, 
                                 console_print_func, debug_log_func)
            if not _execute_pip_command(ACTION_INSTALL, package_name_for_pip, 
                                        console_print_func, debug_log_func):
                missing_packages.append(friendly_name)
        elif not is_installed:
            if not _execute_pip_command(ACTION_INSTALL, package_name_for_pip, 
                                        console_print_func, debug_log_func):
                missing_packages.append(friendly_name)

    # Verification of standard library availability.
    for friendly_name, import_name in BUILTIN_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(friendly_name)

    if missing_packages:
        logger.error(f"🔍📦🔗 [DEPENDENCY] {CRITICAL_FAILURE_MESSAGE}")
        for pkg in missing_packages: 
            logger.error(f"🔍📦🔗 [DEPENDENCY]  - {pkg}")
        if LOCAL_DEBUG:
            logger.info(MANUAL_INSTALL_INSTRUCTION)
        return False
    return True

def run_interactive_pre_check(console_print_func, debug_log_func, 
                              should_clean_install=False):
    """
    Orchestrates the dependency check and triggers process exit on failure.
    """
    if LOCAL_DEBUG:
        logger.info("🔍📦🔗 [DEPENDENCY] Starting dependency check...")
    if not action_check_dependancies(console_print_func, debug_log_func, 
                                     should_clean_install):
        sys.exit(EXIT_CODE_DEPENDENCY_FAILURE)
    if LOCAL_DEBUG:
        logger.success("✅✅✅ [SUCCESS] Dependencies verified.")
