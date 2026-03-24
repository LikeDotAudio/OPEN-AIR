# Managers/DependencyManager.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1855.1
#
# Description: Automated validation and repair of Python library requirements.

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
VERSION = "20260323.1855.1"
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
    "textual": "textual",
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
            
            error_msg = f"❌ [ERROR] Pip {action} failed for {package_name}: {result.stderr.strip()}"
            console_print_func(error_msg)
            logger.error(f"🔍📦🔗 [DEPENDENCY] {error_msg}")
            return False
    except Exception as e:
        error_msg = f"💥 [CRITICAL] Pip execution error: {e}"
        console_print_func(error_msg)
        logger.error(f"🔍📦🔗 [DEPENDENCY] {error_msg}")
        return False

def action_check_dependancies(console_print_func, debug_log_func, 
                              should_clean_install=False, auto_install=True):
    """
    Validates all listed packages and optionally repairs them via pip.
    """
    missing_packages = []
    installed_count = 0
    
    if LOCAL_DEBUG:
        console_print_func("🧐 [INSPECT] Scanning the environment for elite Python modules...")

    for friendly_name, import_name in EXTERNAL_PACKAGES.items():
        # Derive the PyPI package name from the import name unless overridden.
        package_name_for_pip = import_name.split(".")[0]
        
        # --- Package Name Overrides ---
        if friendly_name == "paho-mqtt": package_name_for_pip = "paho-mqtt"
        elif friendly_name == "python-usbtmc": package_name_for_pip = "python-usbtmc"
        elif friendly_name == "python-vxi11": package_name_for_pip = "python-vxi11"
        elif friendly_name == "pyserial": package_name_for_pip = "pyserial"
        elif friendly_name == "beautifulsoup4 (bs4)": package_name_for_pip = "beautifulsoup4"
        elif friendly_name == "Pillow (for support)": package_name_for_pip = "Pillow"
        elif friendly_name == "python-osc": package_name_for_pip = "python-osc"
        elif friendly_name == "python-rtmidi": package_name_for_pip = "python-rtmidi"

        try:
            module = __import__(import_name)
            is_installed = True
            if import_name == "rtmidi":
                if not hasattr(module, "MidiIn"):
                    is_installed = False
        except ImportError:
            is_installed = False

        if is_installed:
            installed_count += 1
            if not should_clean_install:
                console_print_func(f"🌟 [GLORIOUS] Found {friendly_name}! It's here and it's perfect.")
            
            if should_clean_install and auto_install:
                console_print_func(f"🔄 [REFRESH] Re-polishing {friendly_name}...")
                _execute_pip_command(ACTION_UNINSTALL, package_name_for_pip, 
                                     console_print_func, debug_log_func)
                if not _execute_pip_command(ACTION_INSTALL, package_name_for_pip, 
                                            console_print_func, debug_log_func):
                    missing_packages.append(friendly_name)
        elif not is_installed:
            if auto_install:
                console_print_func(f"🛠️ [REPAIR] {friendly_name} is missing! Deploying the engineering team...")
                if not _execute_pip_command(ACTION_INSTALL, package_name_for_pip, 
                                            console_print_func, debug_log_func):
                    missing_packages.append(friendly_name)
            else:
                console_print_func(f"⚠️ [WARNING] {friendly_name} is NOT present in this realm!")
                missing_packages.append(friendly_name)

    # Verification of standard library availability.
    for friendly_name, import_name in BUILTIN_PACKAGES.items():
        try:
            __import__(import_name)
            console_print_func(f"💎 [SOLID] {friendly_name} is baked into the core. Excellent.")
        except ImportError:
            missing_packages.append(friendly_name)

    if missing_packages:
        return False, missing_packages
    
    console_print_func(f"🎉 [TRIUMPH] All {installed_count} dependencies are standing by! We are ready for greatness.")
    return True, []

def run_interactive_pre_check(console_print_func, debug_log_func, 
                              should_clean_install=False, auto_install=True):
    """
    Orchestrates the dependency check and returns True on success, or False on failure.
    """
    success, missing = action_check_dependancies(console_print_func, debug_log_func, 
                                                should_clean_install, auto_install)
    return success

if __name__ == "__main__":
    # If run as a script, perform a standard pre-check.
    run_interactive_pre_check(print, logger.debug)
