# Interface/SetupUI.py
# Author: Anthony Peter Kuzub
# Version: 20260323.1905.1
#
# Description: Textual UI for the OPEN-AIR installation process.

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Log, Label
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
import asyncio
from typing import Coroutine, Any

from oaInstallation.Managers.Setup import (
    SetupManager, STAGE_PYTHON_DEPS, STAGE_MQTT_INFRA, 
    STAGE_SNMP_INFRA, STAGE_DESKTOP_INTEG
)
from oaInstallation.Tests.installation_validator import run_all_tests
from oaInstallation.FileWriters.LogWriter import InstallationLogWriter
from oaInstallation.Core.SystemStats import SystemStatsProvider
from oaInstallation.Workers.runTask import run_background_task

class SetupApp(App):
    """A Textual app to manage the OPEN-AIR installation."""

    CSS = """
    Screen {
        background: #1e1e1e;
    }

    Header {
        background: #F4902C;
        color: #000000;
        text-style: bold;
    }

    #sidebar {
        width: 45;
        background: #2b2b2b;
        border-right: solid #F4902C;
        padding: 1;
    }

    #stats-sidebar {
        width: 42;
        background: #2b2b2b;
        border-left: solid #F4902C;
        padding: 1;
    }

    #main-content {
        padding: 1;
    }

    .status-label {
        margin: 1 0;
        text-style: bold;
        color: #F4902C;
    }

    .status-item {
        margin-left: 2;
        color: #aaaaaa;
    }

    .success {
        color: #00ff00;
    }

    .failure {
        color: #ff0000;
    }

    Button {
        width: 100%;
        margin: 1 0;
    }

    Button.-active {
        background: #F4902C;
        color: #000000;
    }

    #btn_full {
        background: #F4902C;
        color: #000000;
        text-style: bold;
        border: tall #000000;
    }

    Log {
        background: #000000;
        border: solid #F4902C;
        height: 1fr;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f", "full_install", "Full Install"),
    ]

    def __init__(self):
        super().__init__()
        self.manager = SetupManager()
        self.log_writer = InstallationLogWriter()
        self.stats_provider = SystemStatsProvider()
        self.log_lines = []
        self.statuses = {
            STAGE_PYTHON_DEPS: "Pending",
            STAGE_MQTT_INFRA: "Pending",
            STAGE_SNMP_INFRA: "Pending",
            STAGE_DESKTOP_INTEG: "Pending",
            "Tests": "Pending"
        }

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Installation Stages", classes="status-label")
                self.dep_status = Label(f"📦 {STAGE_PYTHON_DEPS}: Pending", classes="status-item")
                yield self.dep_status
                self.mqtt_status = Label(f"📡 {STAGE_MQTT_INFRA}: Pending", classes="status-item")
                yield self.mqtt_status
                self.snmp_status = Label(f"🛠️ {STAGE_SNMP_INFRA}: Pending", classes="status-item")
                yield self.snmp_status
                self.desk_status = Label(f"🖥️ {STAGE_DESKTOP_INTEG}: Pending", classes="status-item")
                yield self.desk_status
                self.test_status = Label("🧪 System Tests: Pending", classes="status-item")
                yield self.test_status
                
                yield Label("Actions", classes="status-label")
                yield Button("Run Dependency Check", id="btn_deps", variant="primary")
                yield Button("Clean Installation", id="btn_clean", variant="error")
                yield Button("Setup MQTT/SNMP", id="btn_infra", variant="primary")
                yield Button("Setup Desktop Icon", id="btn_desktop", variant="primary")
                yield Button("Run Validation Tests", id="btn_tests", variant="primary")
                yield Button("Full Installation", id="btn_full", variant="success")

            with Vertical(id="main-content"):
                yield Label("Installation Log")
                self.installation_log = Log()
                yield self.installation_log

            with Vertical(id="stats-sidebar"):
                yield Label("System Metrics", classes="status-label")
                self.cpu_label = Label("CPU: -- MHz", classes="status-item")
                yield self.cpu_label
                self.ram_label = Label("RAM: --%", classes="status-item")
                yield self.ram_label
                self.disk_label = Label("Disk: -- GB free", classes="status-item")
                yield self.disk_label

        yield Footer()

    def on_mount(self) -> None:
        """Initializes timers on app mount."""
        self.set_interval(2.0, self.update_stats)

    def update_stats(self) -> None:
        """Periodic task to refresh system stats."""
        stats = self.stats_provider.get_all_stats()
        self.cpu_label.update(f"⚡ CPU Speed: [bold #F4902C]{stats['cpu_mhz']:.0f} MHz[/]")
        self.ram_label.update(f"🧠 RAM Usage: [bold #F4902C]{stats['ram_percent']}%[/] ({stats['ram_used_gb']:.1f}/{stats['ram_total_gb']:.1f} GB)")
        self.disk_label.update(f"💿 Disk Free: [bold #F4902C]{stats['disk_free_gb']:.1f} GB[/] ({stats['disk_percent']:.1f}%)")

    def write_log(self, message: str) -> None:
        """Helper to write to UI log and local buffer."""
        self.installation_log.write_line(message)
        self.log_lines.append(message)

    def run_task(self, coro: Coroutine[Any, Any, Any], group: str = "default") -> None:
        """Helper to run a coroutine as a Textual background task."""
        self.run_worker(coro, group=group, thread=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_deps":
            self.run_task(self.check_dependencies())
        elif event.button.id == "btn_clean":
            self.run_task(self.perform_clean_install())
        elif event.button.id == "btn_infra":
            self.run_task(self.setup_infrastructure())
        elif event.button.id == "btn_desktop":
            self.run_task(self.setup_desktop())
        elif event.button.id == "btn_tests":
            self.run_task(self.run_validation())
        elif event.button.id == "btn_full":
            self.run_task(self.full_installation())

    async def perform_clean_install(self):
        """
        Specialized routine to wipe and refresh all dependencies.
        Uses a two-step log-based confirmation.
        """
        if not hasattr(self, "_clean_confirm") or not self._clean_confirm:
            self.write_log("🚨 [CRITICAL] YOU HAVE REQUESTED A CLEAN INSTALLATION!")
            self.write_log("🛑 [WARNING] This will UNINSTALL and RE-INSTALL all elite packages.")
            self.write_log("🤔 [CONFIRM] Are you absolutely sure? Click 'Clean Installation' again to proceed.")
            self._clean_confirm = True
            self.query_one("#btn_clean").label = "CONFIRM: CLEAN INSTALL"
            return

        # Reset confirmation
        self._clean_confirm = False
        self.query_one("#btn_clean").label = "Clean Installation"

        self.write_log("🌪️ [PURGE] Initiating full environmental scrub...")
        try:
            success = await asyncio.to_thread(self.manager.check_dependencies, self.write_log, auto_install=True, clean_install=True)
            
            if success:
                self.dep_status.update(f"📦 {STAGE_PYTHON_DEPS}: [green]Refreshed[/]")
                self.write_log("✨ [POLISHED] All dependencies have been purged and perfectly re-installed!")
            else:
                self.dep_status.update(f"📦 {STAGE_PYTHON_DEPS}: [red]Repair Failed[/]")
                self.write_log("💀 [FAILURE] The purge was successful, but the re-population failed!")
        except Exception as e:
            self.write_log(f"💥 [CRITICAL ERROR] The scrub process crashed: {e}")
            self.dep_status.update(f"📦 {STAGE_PYTHON_DEPS}: [red]CRASHED[/]")
            success = False
        
        return success

    async def check_dependencies(self):
        self.write_log("🕵️ [MISSION] Initiating deep scan for legendary dependencies...")
        
        # First check without auto-installing
        success = await asyncio.to_thread(self.manager.check_dependencies, self.write_log, auto_install=False)
        
        if success:
            self.dep_status.update(f"📦 {STAGE_PYTHON_DEPS}: [green]Glorious[/]")
            self.write_log("🎆 [CELEBRATION] Every single package is in place! This environment is impeccable.")
        else:
            self.dep_status.update(f"📦 {STAGE_PYTHON_DEPS}: [yellow]Incomplete[/]")
            self.write_log("😲 [SCANDAL] We are missing some essential components!")
            self.write_log("🤔 [INQUIRY] Should I deploy the engineering team to install the missing pieces?")
            self.write_log("💡 Tip: Click 'Run Dependency Check' again to attempt auto-repair.")
            
            # Change button text to indicate next step
            self.query_one("#btn_deps").label = "Attempt Auto-Repair"
            self.query_one("#btn_deps").variant = "warning"
            
            # If they click again, we should detect this state
            if hasattr(self, "_dep_check_failed") and self._dep_check_failed:
                await self.install_missing_dependencies()
                self._dep_check_failed = False
                self.query_one("#btn_deps").label = "Run Dependency Check"
                self.query_one("#btn_deps").variant = "primary"
            else:
                self._dep_check_failed = True
                
        return success

    async def install_missing_dependencies(self):
        self.write_log("🏗️ [CONSTRUCTION] Engineering team deployed! Repairing the environment...")
        success = await asyncio.to_thread(self.manager.check_dependencies, self.write_log, auto_install=True)
        if success:
            self.dep_status.update(f"📦 {STAGE_PYTHON_DEPS}: [green]Repaired[/]")
            self.write_log("🏆 [TRIUMPH] Environment restored to its former glory!")
        else:
            self.write_log("💀 [DISASTER] Even our best engineers couldn't fix this. Manual intervention required.")
        return success

    async def setup_infrastructure(self):
        self.write_log("🚀 [MISSION] Provisioning world-class infrastructure...")
        
        mqtt_success = await asyncio.to_thread(self.manager.setup_mqtt, self.write_log)
        self.mqtt_status.update(f"📡 {STAGE_MQTT_INFRA}: {'[green]Installed[/]' if mqtt_success else '[red]Failed[/]'}")
        
        snmp_success = await asyncio.to_thread(self.manager.setup_snmp, self.write_log)
        self.snmp_status.update(f"🛠️ {STAGE_SNMP_INFRA}: {'[green]Installed[/]' if snmp_success else '[red]Failed[/]'}")
        
        if mqtt_success and snmp_success:
            self.write_log("💎 [ELITE] Infrastructure is robust and ready for traffic.")
        
        return mqtt_success and snmp_success

    async def setup_desktop(self):
        self.write_log("🚀 [MISSION] Integrating with the master desktop environment...")
        success = await asyncio.to_thread(self.manager.setup_desktop, self.write_log)
        self.desk_status.update(f"🖥️ {STAGE_DESKTOP_INTEG}: {'[green]Complete[/]' if success else '[red]Failed[/]'}")
        if success:
            self.write_log("🎨 [STYLISH] The OPEN-AIR icon is now a permanent fixture of your workspace.")
        return success

    async def run_validation(self):
        self.write_log("🚀 [MISSION] Performing final high-stakes validation...")
        success = await asyncio.to_thread(run_all_tests, self.write_log)
        self.test_status.update(f"🧪 System Tests: {'[green]Passed[/]' if success else '[red]Failed[/]'}")
        if success:
            self.write_log("🥇 [PRESTIGE] All systems have passed rigorous testing. We are GO for launch.")
        else:
            self.write_log("⚠️ [ANOMALY] Validation failed! Minor adjustments may be needed.")
        return success

    async def full_installation(self):
        self.write_log("🔥 [IGNITION] Starting FULL INSTALLATION process...")
        
        # Check dependencies first
        success = await asyncio.to_thread(self.manager.check_dependencies, self.write_log, auto_install=False)
        if not success:
            self.write_log("❓ [CHOICE] Dependencies are missing. Proceeding with automatic repair...")
            success = await self.install_missing_dependencies()
            
        if success:
            if await self.setup_infrastructure():
                if await self.setup_desktop():
                    await self.run_validation()
                    self.write_log("🏆 [LEGENDARY] FULL INSTALLATION COMPLETE! The system is magnificent.")
                    
                    # Save the log content to the configuration directory
                    log_content = "\n".join(self.log_lines)
                    success = self.log_writer.write_log(log_content)
                    if success:
                        self.write_log(f"💾 [SECURE] Log archived at: {self.log_writer.get_log_path()}")
                    else:
                        self.write_log("⚠️ [WARNING] Failed to archive the victory log.")
                else:
                    self.write_log("🛑 [HALT] Desktop integration failed.")
            else:
                self.write_log("🛑 [HALT] Infrastructure setup failed.")
        else:
            self.write_log("🛑 [HALT] Dependency check failed. Aborting full install.")

if __name__ == "__main__":
    app = SetupApp()
    app.run()
