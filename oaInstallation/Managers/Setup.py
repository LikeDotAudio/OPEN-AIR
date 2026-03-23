# Managers/Setup.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1830.1
#
# Description: Primary installation orchestrator for the OPEN-AIR system environment.
# This script ensures all Python dependencies and system infrastructure are present.

import os
import sys
import subprocess
import shutil

# --- Path Injection ---
# We resolve the project root and inject it into sys.path immediately to ensure
# that internal modules can be imported regardless of
# how or where this script is executed.
def _inject_project_root():
    """Calculates and injects the project root into sys.path."""
    # Current file: project_root/oaInstallation/Managers/Setup.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root

PROJECT_ROOT = _inject_project_root()

# Now we can safely import loguru and other internal modules
from loguru import logger

# --- Constants ---
VERSION = "20260323.1830.1"
EXIT_CODE_CRITICAL = 1

# Stage Indicators for consistent logging
STAGE_PYTHON_DEPS = "Python Dependencies"
STAGE_MQTT_INFRA = "MQTT Infrastructure"
STAGE_SNMP_INFRA = "SNMP Infrastructure"
STAGE_DESKTOP_INTEG = "Desktop Integration"

class SetupManager:
    """
    Core manager for the OPEN-AIR installation process.
    Orchestrates dependency checks and system infrastructure deployment.
    """
    def __init__(self, debug=True):
        self.debug = debug
        self.project_root = PROJECT_ROOT

    def check_dependencies(self, callback=None, auto_install=True, clean_install=False):
        """
        Invokes the automated dependency checker.
        """
        try:
            # Import DependencyManager from the local Managers directory
            from oaInstallation.Managers import DependencyManager as dependancy_checker
            
            def log_proxy(message, **kwargs):
                if callback: callback(message)
                elif self.debug: logger.debug(f"🛠️⚙️📦 [SETUP] {message}")

            # Run the pre-check which validates and repairs missing packages
            success = dependancy_checker.run_interactive_pre_check(
                lambda m: callback(m) if callback else logger.info(m),
                log_proxy,
                should_clean_install=clean_install,
                auto_install=auto_install
            )
            return success
        except Exception as e:
            logger.error(f"🛠️⚙️📦 [SETUP] Dependency check failed: {e}")
            return False

    def setup_mqtt(self, callback=None):
        """Ensures Mosquitto broker is installed and available."""
        if shutil.which('mosquitto'):
            if callback: callback("Mosquitto broker is active.")
            return True
        
        if callback: callback("Mosquitto missing. Attempting install...")
        try:
            # We use check=False for update as it might fail on some networks but
            # still allow the install to proceed.
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', 'mosquitto', '-y'], check=True)
            if callback: callback("Mosquitto deployed successfully.")
            return True
        except Exception as e:
            if callback: callback(f"Mosquitto install failed: {e}")
            return False

    def setup_snmp(self, callback=None):
        """Ensures SNMP daemon and utilities are installed."""
        if shutil.which('snmpd'):
            if callback: callback("SNMP daemon is active.")
            return True
        
        if callback: callback("SNMP missing. Attempting install...")
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', 'snmpd', 'snmp', '-y'], check=True)
            if callback: callback("SNMP deployed successfully.")
            return True
        except Exception as e:
            if callback: callback(f"SNMP install failed: {e}")
            return False

    def setup_desktop(self, callback=None):
        """
        Installs the application's desktop entry and pins it to the taskbar.
        """
        # TaskBarIcon.py is located in the sibling Core directory
        taskbar_script = os.path.join(self.project_root, "oaInstallation", "Core", "TaskBarIcon.py")
        
        if not os.path.exists(taskbar_script):
            error_msg = f"Error: {taskbar_script} not found."
            if callback: callback(error_msg)
            logger.error(f"🛠️⚙️📦 [SETUP] {error_msg}")
            return False

        try:
            # Run the taskbar icon installer as a separate process
            subprocess.run([sys.executable, taskbar_script], check=True)
            if callback: callback("Desktop integration complete.")
            return True
        except Exception as e:
            if callback: callback(f"Desktop integration failed: {e}")
            return False

def main():
    """Primary entry point for the Setup utility."""
    manager = SetupManager()
    
    logger.info(f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_PYTHON_DEPS}")
    if not manager.check_dependencies():
        logger.error("🛑 [CRITICAL] Dependency check failed. Setup aborted.")
        sys.exit(EXIT_CODE_CRITICAL)

    logger.info(f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_MQTT_INFRA}")
    manager.setup_mqtt()

    logger.info(f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_SNMP_INFRA}")
    manager.setup_snmp()

    logger.info(f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_DESKTOP_INTEG}")
    manager.setup_desktop()

    logger.success("✅✅✅ [SUCCESS] Setup complete.")

if __name__ == "__main__":
    main()
