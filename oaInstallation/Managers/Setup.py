# Managers/Setup.py
# Author: Anthony Peter Kuzub
# Version: 20260314.002500.REV01
#
# Description: Primary installation orchestrator for the OPEN-AIR system environment.

"""
Primary Purpose:
This script acts as the master setup utility, coordinating the installation of
system-level dependencies (Mosquitto, SNMP), Python packages, and desktop
integration components.
"""

import os
import sys
import subprocess
import shutil

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger

# Specialized logger instance bound to the 'SETUP' subsystem.
setup_logger = logger.bind(subsystem="SETUP")

# --- Constants ---
VERSION = "20260314.002500.REV01"
EXIT_CODE_CRITICAL = 1

# Stage Indicators for logging/process tracking
STAGE_PYTHON_DEPS = 1
STAGE_MQTT_INFRA = 2
STAGE_SNMP_INFRA = 3
STAGE_DESKTOP_INTEG = 4

def main():
    """
    Orchestrates the multi-stage installation and configuration sequence.
    """
    # Establish the logical root of the project for relative importing.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Inject project root into the path to enable 'oaDependencies' 
    # imports.
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    if LOCAL_DEBUG:
        logger.debug(f"🛠️⚙️📦 [SETUP] Project root resolved: {project_root}")

    # --- 1. Run Dependency Check ---
    if LOCAL_DEBUG:
        logger.info(f"🛠️⚙️📦 [SETUP] --- Stage {STAGE_PYTHON_DEPS}: Python Dependencies ---")
    try:
        from oaDependencies import dependancy_checker
        
        # Define a zero-cost debug proxy for the dependency engine
        def setup_debug_log(message, **kwargs):
            if LOCAL_DEBUG:
                logger.debug(f"🛠️⚙️📦 [SETUP] {message}")

        # Execute interactive check; allows for automated repair if needed.
        dependancy_checker.run_interactive_pre_check(
            logger.info, 
            setup_debug_log, 
            should_clean_install=False
        )
        
    except ImportError as import_error:
        # Gravity of Errors: Critical failure if internal setup modules are lost.
        logger.error(f"🛠️⚙️📦 [SETUP] CRITICAL: Setup modules missing: {import_error}")
        sys.exit(EXIT_CODE_CRITICAL)
    except Exception:
        # Capture full forensic report for unexpected installation logic errors.
        logger.exception("🛠️⚙️📦 [SETUP] CRITICAL: Dependency check crashed.")
        sys.exit(EXIT_CODE_CRITICAL)

    # --- 1.5 Check for Mosquitto Broker ---
    if LOCAL_DEBUG:
        logger.info(f"🛠️⚙️📦 [SETUP] --- Stage {STAGE_MQTT_INFRA}: MQTT Infrastructure ---")
    
    if shutil.which('mosquitto'):
        if LOCAL_DEBUG:
            logger.success("✅✅✅ [SUCCESS] Mosquitto broker is active.")
    else:
        logger.warning("🛠️⚙️📦 [SETUP] Mosquitto missing. Attempting install...")
        try:
            # APT-GET utilized for standardized Debian package management.
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', 'mosquitto', '-y'], 
                           check=True)
            logger.success("✅✅✅ [SUCCESS] Mosquitto deployed.")
        except subprocess.CalledProcessError as process_error:
            logger.error(f"🛠️⚙️📦 [SETUP] ERROR: Mosquitto failure ({process_error.returncode}).")
        except FileNotFoundError:
            logger.error("🛠️⚙️📦 [SETUP] ERROR: 'apt-get' binary not found.")

    # --- 1.6 Check for SNMP Daemon ---
    if LOCAL_DEBUG:
        logger.info(f"🛠️⚙️📦 [SETUP] --- Stage {STAGE_SNMP_INFRA}: SNMP Infrastructure ---")
    if shutil.which('snmpd'):
        if LOCAL_DEBUG:
            logger.success("✅✅✅ [SUCCESS] SNMP daemon is active.")
    else:
        logger.warning("🛠️⚙️📦 [SETUP] SNMP missing. Attempting install...")
        try:
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', 'snmpd', 'snmp', '-y'], 
                           check=True)
            logger.success("✅✅✅ [SUCCESS] SNMP deployed.")
        except subprocess.CalledProcessError as process_error:
            logger.error(f"🛠️⚙️📦 [SETUP] ERROR: SNMP failure ({process_error.returncode}).")
        except FileNotFoundError:
            logger.error("🛠️⚙️📦 [SETUP] ERROR: 'apt-get' binary not found.")

    # --- 2. Run TaskBar Icon Setup ---
    if LOCAL_DEBUG:
        logger.info(f"🛠️⚙️📦 [SETUP] --- Stage {STAGE_DESKTOP_INTEG}: Desktop Integration ---")
    taskbar_script = os.path.join(current_dir, 'TaskBarIcon.py')
    
    if os.path.exists(taskbar_script):
        if LOCAL_DEBUG:
            logger.debug(f"🛠️⚙️📦 [SETUP] Executing {taskbar_script}...")
        try:
            # Subprocess isolation used to prevent script state leakage.
            subprocess.run([sys.executable, taskbar_script], check=True)
            logger.success("✅✅✅ [SUCCESS] Desktop integration complete.")
        except subprocess.CalledProcessError as process_error:
            logger.error(f"🛠️⚙️📦 [SETUP] ERROR: Icon setup failed ({process_error.returncode}).")
    else:
        logger.error(f"🛠️⚙️📦 [SETUP] ERROR: {taskbar_script} not found.")

    if LOCAL_DEBUG:
        logger.success("✅✅✅ [SUCCESS] Setup sequence complete. Launch via ./OpenAir.py")

if __name__ == "__main__":
    main()
