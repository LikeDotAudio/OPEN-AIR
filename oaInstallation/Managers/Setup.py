import os
import sys

# 1. Setup Environment: Ensure the project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import inspect
import shutil

# Managers/Setup.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1830.1
#
# Description: Primary installation orchestrator for the OPEN-AIR system environment.
# This script ensures all Python dependencies and system infrastructure are present.
import subprocess

from oaLogging.Methods.matrix_gate import matrix_log


# --- Path Injection ---
# We resolve the project root and inject it into sys.path immediately to ensure
# that internal modules can be imported regardless of
# how or where this script is executed.
def _inject_project_root():
    """Calculates and injects the project root into sys.path."""
    # Current file: project_root/oaInstallation/Managers/Setup.py
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
    def __init__(self, project_root=None, debug=True):
        self.debug = debug
        self.project_root = project_root or PROJECT_ROOT
        matrix_log("core", "setup", "__init__", f"🛠️⚙️📦 [SETUP] SetupManager initialized with project_root: {self.project_root}", "DEBUG")
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
            if callback: callback("⚡ [POWER] Mosquitto broker is buzzing with energy!")
            return True

        if callback: callback("📡 [SEARCH] Mosquitto missing. Attempting heroic install...")
        try:
            # We use check=False for update as it might fail on some networks but
            # still allow the install to proceed.
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', 'mosquitto', '-y'], check=True)
            if callback: callback("✨ [SUCCESS] Mosquitto deployed magnificently.")
            return True
        except Exception as e:
            if callback: callback(f"💀 [FAILURE] Mosquitto install failed catastrophically: {e}")
            return False

    def setup_snmp(self, callback=None):
        """Ensures SNMP daemon is installed and CONFIGURED."""
        if shutil.which('snmpd'):
            # Check if our 'pass' configuration exists in snmpd.conf
            try:
                with open('/etc/snmp/snmpd.conf') as f:
                    if 'pass .1.3.6.1.4.1.65300' in f.read():
                        if callback: callback("📡 [RADAR] SNMP daemon is active and configured!")
                        return True
            except Exception:
                pass # Proceed to install/re-config

        if callback: callback("🛠️ [REPAIR] SNMP missing or unconfigured. Initiating deployment sequence...")
        try:
            # 1. Ensure packages are present
            subprocess.run(['sudo', 'apt-get', 'update'], check=False)
            subprocess.run(['sudo', 'apt-get', 'install', 'snmpd', 'snmp', 'snmp-mibs-downloader', '-y'], check=True)

            # 2. Use SNMPManager to generate the master installer script
            from oaComProtocols.oaComSNMP.Managers.snmp_manager import SNMPManager
            snmp_mgr = SNMPManager(run_bridge=True)
            snmp_mgr.tree_builder.generate_master_script()
            installer_bash = snmp_mgr.get_installer_script()

            installer_path = os.path.join(getattr(self, 'project_root', PROJECT_ROOT), "oaComProtocols", "oaComSNMP", "Assets", "snmp_install_tmp.sh")
            os.makedirs(os.path.dirname(installer_path), exist_ok=True)

            with open(installer_path, "w") as f:
                f.write(installer_bash)
            os.chmod(installer_path, 0o755)

            # 3. Execute the installer
            if callback: callback("⚙️ [CONFIG] Applying master OID tree configuration...")
            # We must run this as root since it touches /etc/snmp/
            subprocess.run(['sudo', installer_path], cwd=getattr(self, 'project_root', PROJECT_ROOT), check=True)

            if callback: callback("✨ [SUCCESS] SNMP infrastructure deployed and configured.")
            return True
        except Exception as e:
            if callback: callback(f"💀 [FAILURE] SNMP deployment failed: {e}")
            return False

    def setup_desktop(self, callback=None):
        """
        Installs the application's desktop entry and pins it to the taskbar.
        """
        # TaskBarIcon.py is located in the sibling Core directory
        taskbar_script = os.path.join(getattr(self, 'project_root', PROJECT_ROOT), "oaInstallation", "Core", "TaskBarIcon.py")

        if not os.path.exists(taskbar_script):
            error_message = f"Error: {taskbar_script} not found."
            if callback: callback(f"💀 [MISSING] {error_message}")
            logger.error(f"🛠️⚙️📦 [SETUP] {error_message}")
            return False

        try:
            # Run the taskbar icon installer as a separate process
            subprocess.run([sys.executable, taskbar_script], check=True)
            if callback: callback("🎨 [AESTHETICS] Desktop integration completed with flawless style.")
            return True
        except Exception as e:
            if callback: callback(f"💀 [FAILURE] Desktop integration crashed: {e}")
            return False

    def setup_rust_core(self, callback=None):
        """Builds and installs the centralized high-performance Rust core."""
        rust_core_dir = os.path.join(getattr(self, 'project_root', PROJECT_ROOT), "oaRustCore")

        if not os.path.exists(rust_core_dir):
            if callback: callback("⚠️ [SKIP] oaRustCore directory not found. Skipping native build.")
            return True

        if callback: callback("🏗️ [BUILD] Compiling centralized Rust core... this may take a moment.")
        try:
            # ⚡ PERFORMANCE: We use 'maturin develop' for local JIT-like compilation
            env = os.environ.copy()
            env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"
            subprocess.check_call(["maturin", "develop"], cwd=rust_core_dir, env=env)
            if callback: callback("✨ [SUCCESS] High-performance Rust pipeline is now active.")
            return True
        except Exception as e:
            if callback: callback(f"💀 [FAILURE] Rust compilation failed: {e}")
            return False

def main():
    """Primary entry point for the Setup utility."""
    manager = SetupManager(project_root=PROJECT_ROOT)

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_PYTHON_DEPS}", "INFO")
    if not manager.check_dependencies():
        logger.error("🛑 [CRITICAL] Dependency check failed. Setup aborted.")
        sys.exit(EXIT_CODE_CRITICAL)

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🛠️⚙️📦 [SETUP] Starting Stage: Native Rust Core", "INFO")
    manager.setup_rust_core(lambda m: logger.info(m))

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_MQTT_INFRA}", "INFO")
    manager.setup_mqtt()

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_SNMP_INFRA}", "INFO")
    manager.setup_snmp()

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🛠️⚙️📦 [SETUP] Starting Stage: {STAGE_DESKTOP_INTEG}", "INFO")
    manager.setup_desktop()

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅✅✅ [SUCCESS] Setup complete.", "SUCCESS")

if __name__ == "__main__":
    main()
