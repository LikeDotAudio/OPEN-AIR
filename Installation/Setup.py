# Installation/Setup.py
#
# Primary installation orchestrator for the OPEN-AIR system environment.
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
# Version 20260314.002500.REV01

"""
Primary Purpose:
This script acts as the master setup utility, coordinating the installation of
system-level dependencies (Mosquitto, SNMP), Python packages, and desktop
integration components. It ensures the host environment is correctly configured
before the main application is launched.

Hard Constraints:
- Platform Dependency: Targeted at Debian-based Linux distributions (utilizes
  'apt-get').
- Privileges: Requires 'sudo' privileges for system package installation.
- System State: Assumes an active internet connection for package retrieval.
"""

import os
import sys
import subprocess
import traceback

# --- Standard Debug Logging Setup ---
# LOCAL_DEBUG: Toggles verbose logging for the master setup process.
LOCAL_DEBUG = True
from loguru import logger

# Specialized logger instance bound to the 'SETUP' subsystem.
setup_logger = logger.bind(subsystem="SETUP")

def main():
    """
    Orchestrates the multi-stage installation and configuration sequence.

    Lead with action: Executes dependency checks, system package deployment,
    and desktop integration in a predefined order to satisfy system
    requirements.

    Inputs:
        None.

    Outputs:
        None. The process may exit with code 1 upon encountering a critical,
        unrecoverable failure.

    Side Effects:
        - Modifies 'sys.path' to include the project root.
        - Executes multiple external subprocesses (apt-get, TaskBarIcon.py).
        - Modifies global system state by installing software packages.
    
    Thread Safety:
        Not thread-safe. Should only be executed as a standalone entry point.
    """
    # Establish the logical root of the project for relative importing.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Inject project root into the path to enable 'Installation.dependancy' 
    # imports.
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    if LOCAL_DEBUG:
        logger.debug(f"🛠️⚙️📦 [SETUP] Project root resolved: {project_root}")

    # --- 1. Run Dependency Check ---
    # This phase verifies the presence of required Python libraries.
    if LOCAL_DEBUG:
        logger.info("🛠️⚙️📦 [SETUP] --- Stage 1: Python Dependencies ---")
    try:
        from Installation.dependancy import dependancy_checker
        
        # Define a zero-cost debug proxy for the dependency engine to maintain
        # standardized formatting.
        def setup_debug_log(message, **kwargs):
            if LOCAL_DEBUG:
                logger.debug(f"🛠️⚙️📦 [SETUP] {message}")

        # Execute interactive check; allows for automated repair if needed.
        dependancy_checker.run_interactive_pre_check(
            logger.info, 
            setup_debug_log, 
            should_clean_install=False
        )
        
    except ImportError as e:
        # Gravity of Errors: Critical failure if internal setup modules are lost.
        logger.error(f"🛠️⚙️📦 [SETUP] CRITICAL: Setup modules missing: {e}")
        sys.exit(1)
    except Exception:
        # Capture full forensic report for unexpected installation logic errors.
        logger.exception("🛠️⚙️📦 [SETUP] CRITICAL: Dependency check crashed.")
        sys.exit(1)

    # --- 1.5 Check for Mosquitto Broker ---
    # The system relies on MQTT for inter-partition communication.
    if LOCAL_DEBUG:
        logger.info("🛠️⚙️📦 [SETUP] --- Stage 2: MQTT Infrastructure ---")
    import shutil
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
        except subprocess.CalledProcessError as e:
            logger.error(f"🛠️⚙️📦 [SETUP] ERROR: Mosquitto failure ({e.returncode}).")
        except FileNotFoundError:
            logger.error("🛠️⚙️📦 [SETUP] ERROR: 'apt-get' binary not found.")

    # --- 1.6 Check for SNMP Daemon ---
    # SNMP is required for network-based instrument discovery.
    if LOCAL_DEBUG:
        logger.info("🛠️⚙️📦 [SETUP] --- Stage 3: SNMP Infrastructure ---")
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
        except subprocess.CalledProcessError as e:
            logger.error(f"🛠️⚙️📦 [SETUP] ERROR: SNMP failure ({e.returncode}).")
        except FileNotFoundError:
            logger.error("🛠️⚙️📦 [SETUP] ERROR: 'apt-get' binary not found.")

    # --- 2. Run TaskBar Icon Setup ---
    # Final aesthetic integration into the user's desktop environment.
    if LOCAL_DEBUG:
        logger.info("🛠️⚙️📦 [SETUP] --- Stage 4: Desktop Integration ---")
    taskbar_script = os.path.join(current_dir, 'TaskBarIcon.py')
    
    if os.path.exists(taskbar_script):
        if LOCAL_DEBUG:
            logger.debug(f"🛠️⚙️📦 [SETUP] Executing {taskbar_script}...")
        try:
            # Subprocess isolation used to prevent script state leakage.
            subprocess.run([sys.executable, taskbar_script], check=True)
            logger.success("✅✅✅ [SUCCESS] Desktop integration complete.")
        except subprocess.CalledProcessError as e:
            logger.error(f"🛠️⚙️📦 [SETUP] ERROR: Icon setup failed ({e.returncode}).")
    else:
        logger.error(f"🛠️⚙️📦 [SETUP] ERROR: {taskbar_script} not found.")

    if LOCAL_DEBUG:
        logger.success("✅✅✅ [SUCCESS] Setup sequence complete. Launch via ./OpenAir.py")

if __name__ == "__main__":
    main()
