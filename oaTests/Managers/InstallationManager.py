# oaTests/Managers/InstallationManager.py
# Author: Gemini CLI
# Version: 20260404.1400.1
#
# Description: Orchestrates installation and setup tasks for the OPEN-AIR environment within the test UI.

import threading

from oaInstallation.FileWriters.LogWriter import InstallationLogWriter
from oaInstallation.Managers.Setup import SetupManager
from oaInstallation.Tests.test_installation_validator import run_all_tests as run_installation_tests


class InstallationManager:
    """Manages system-wide installation, dependency, and infrastructure setup."""

    def __init__(self, project_root, log_callback):
        self.project_root = project_root
        self.log_callback = log_callback
        self.setup_manager = SetupManager(project_root=self.project_root)
        self.installation_log_writer = InstallationLogWriter()
        self._dep_check_failed = False
        self._clean_confirm = False

    def _run_in_thread(self, task_func):
        thread = threading.Thread(target=task_func, daemon=True)
        thread.start()

    def perform_dep_check(self):
        def task():
            self.log_callback("🕵️ [MISSION] Initiating deep scan for legendary dependencies...")
            success = self.setup_manager.check_dependencies(self.log_callback, auto_install=False)

            if success:
                self.log_callback("🎆 [CELEBRATION] Every single package is in place! This environment is impeccable.")
            else:
                self.log_callback("😲 [SCANDAL] We are missing some essential components!")
                if self._dep_check_failed:
                    self.log_callback("🏗️ [CONSTRUCTION] Engineering team deployed! Repairing the environment...")
                    success = self.setup_manager.check_dependencies(self.log_callback, auto_install=True)
                    if success:
                        self.log_callback("🏆 [TRIUMPH] Environment restored to its former glory!")
                    else:
                        self.log_callback("💀 [DISASTER] Even our best engineers couldn't fix this. Manual intervention required.")
                    self._dep_check_failed = False
                else:
                    self.log_callback("🤔 [INQUIRY] Should I deploy the engineering team to install the missing pieces?")
                    self.log_callback("💡 Tip: Click 'Run Dependency Check' again to attempt auto-repair.")
                    self._dep_check_failed = True

        self._run_in_thread(task)

    def perform_clean_install(self):
        def task():
            if not self._clean_confirm:
                self.log_callback("🚨 [CRITICAL] YOU HAVE REQUESTED A CLEAN INSTALLATION!")
                self.log_callback("🛑 [WARNING] This will UNINSTALL and RE-INSTALL all elite packages.")
                self.log_callback("🤔 [CONFIRM] Are you absolutely sure? Click 'Clean Installation' again to proceed.")
                self._clean_confirm = True
                return

            self._clean_confirm = False
            self.log_callback("🌪️ [PURGE] Initiating full environmental scrub...")
            try:
                success = self.setup_manager.check_dependencies(self.log_callback, auto_install=True, clean_install=True)
                if success:
                    self.log_callback("✨ [POLISHED] All dependencies have been purged and perfectly re-installed!")
                else:
                    self.log_callback("💀 [FAILURE] The purge was successful, but the re-population failed!")
            except Exception as e:
                self.log_callback(f"💥 [CRITICAL ERROR] The scrub process crashed: {e}")

        self._run_in_thread(task)

    def perform_infra_setup(self):
        def task():
            self.log_callback("🚀 [MISSION] Provisioning world-class infrastructure...")
            mqtt_success = self.setup_manager.setup_mqtt(self.log_callback)
            snmp_success = self.setup_manager.setup_snmp(self.log_callback)
            if mqtt_success and snmp_success:
                self.log_callback("💎 [ELITE] Infrastructure is robust and ready for traffic.")

        self._run_in_thread(task)

    def perform_desktop_setup(self):
        def task():
            self.log_callback("🚀 [MISSION] Integrating with the master desktop environment...")
            success = self.setup_manager.setup_desktop(self.log_callback)
            if success:
                self.log_callback("🎨 [STYLISH] The OPEN-AIR icon is now a permanent fixture of your workspace.")

        self._run_in_thread(task)

    def perform_install_validation(self):
        def task():
            self.log_callback("🚀 [MISSION] Performing final high-stakes validation...")
            success = run_installation_tests(self.log_callback)
            if success:
                self.log_callback("🥇 [PRESTIGE] All systems have passed rigorous testing. We are GO for launch.")
            else:
                self.log_callback("⚠️ [ANOMALY] Validation failed! Minor adjustments may be needed.")

        self._run_in_thread(task)

    def perform_full_installation(self, log_lines_getter):
        def task():
            self.log_callback("🔥 [IGNITION] Starting FULL INSTALLATION process...")
            success = self.setup_manager.check_dependencies(self.log_callback, auto_install=False)
            if not success:
                self.log_callback("🏗️ [CONSTRUCTION] Engineering team deployed! Repairing the environment...")
                success = self.setup_manager.check_dependencies(self.log_callback, auto_install=True)

            if success:
                mqtt_ok = self.setup_manager.setup_mqtt(self.log_callback)
                snmp_ok = self.setup_manager.setup_snmp(self.log_callback)
                if mqtt_ok and snmp_ok:
                    if self.setup_manager.setup_desktop(self.log_callback):
                        run_installation_tests(self.log_callback)
                        self.log_callback("🏆 [LEGENDARY] FULL INSTALLATION COMPLETE! The system is magnificent.")
                        log_content = "\n".join(log_lines_getter())
                        if self.installation_log_writer.write_log(log_content):
                            self.log_callback(f"💾 [SECURE] Log archived at: {self.installation_log_writer.get_log_path()}")
                    else:
                        self.log_callback("🛑 [HALT] Desktop integration failed.")
                else:
                    self.log_callback("🛑 [HALT] Infrastructure setup failed.")
            else:
                self.log_callback("🛑 [HALT] Dependency check failed. Aborting full install.")

        self._run_in_thread(task)
