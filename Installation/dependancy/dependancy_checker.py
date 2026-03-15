# Installation/dependancy/dependancy_checker.py
#
# Automated validation and repair of Python library requirements.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your
# specific application can be negotiated. There is no charge to use, modify,
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260314.004000.REV01

"""
Primary Purpose:
This module manages the identification, verification, and automated installation
 of third-party Python packages required for the OPEN-AIR platform. It abstracts
 the underlying 'pip' commands and handles environmental edge cases (such as
 package name conflicts).

Hard Constraints:
- Execution Privilege: May require administrative rights to install packages
  depending on the environment.
- System State: Assumes connectivity to the Python Package Index (PyPI).
- Tooling: Depends on the availability of the 'pip' module in the current Python
  interpreter.
"""

import os
import sys
import inspect
import subprocess
import pathlib

# --- Standard Debug Logging Setup ---
# LOCAL_DEBUG: Toggles verbose logging for the dependency validation lifecycle.
LOCAL_DEBUG = True
from loguru import logger

current_file = f"{os.path.basename(__file__)}"
current_version = "20260131.000000.1"

# --- Constants ---
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

    Lead with action: Executes a subprocess call to 'pip' using the current
    Python interpreter to ensure the target environment is correctly modified.

    Inputs:
        action (str): The pip command to run ('install' or 'uninstall').
        package_name (str): The exact name of the package on PyPI.
        console_print_func (callable): Function for visible status reporting.
        debug_log_func (callable): Function for detailed diagnostic logging.

    Outputs:
        bool: True if the operation succeeded or was already in the target 
              state; False if pip returned a non-zero exit code.

    Side Effects:
        - Spawns an external 'pip' process.
        - Modifies the local Python site-packages directory.
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

    Lead with action: Scans the current import registry for every package 
    defined in 'EXTERNAL_PACKAGES'. If a package is missing, it attempts an
    automated installation.

    Inputs:
        console_print_func (callable): Sink for primary status messages.
        debug_log_func (callable): Sink for verbose tracing.
        should_clean_install (bool): If True, uninstalls then reinstalls
            every package to ensure fresh state. Defaults to False.

    Outputs:
        bool: True if all dependencies are satisfied; False if one or more
              packages remain missing or failed to install.

    Side Effects:
        - Dynamically imports modules to verify existence.
        - May modify filesystem state via '_execute_pip_command'.
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

    Inputs:
        See 'action_check_dependancies'.
    """
    if LOCAL_DEBUG:
        logger.info("🔍📦🔗 [DEPENDENCY] Starting dependency check...")
    if not action_check_dependancies(console_print_func, debug_log_func, 
                                     should_clean_install):
        sys.exit(1)
    if LOCAL_DEBUG:
        logger.success("✅✅✅ [SUCCESS] Dependencies verified.")
