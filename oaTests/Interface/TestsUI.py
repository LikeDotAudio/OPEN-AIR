# oaTests/Interface/TestsUI.py
#
# High-fidelity Textual TUI for the OPEN-AIR testing and maintenance suite.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260426.1348.1
#
# Description:
# This module implements the main Textual application for managing the
# OPEN-AIR test suite. It uses MaintenanceManager and InstallationManager
# to handle specialized background tasks.

import os
import signal
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime

# Import worker logic
from oaTests.Core.Workers.TestRunner import TestRunner
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Label

from oaComProtocols.oaComMQTT.Entry import get_connection_manager
from oaGuiEditorWYSIWYG.Entry import launch_editor
from oaInstallation.Core.SystemStats import SystemStatsProvider
from oaLogging.Entry import TEST_LOGGER
from oaTests.Managers.AuditRunner import run_all_audits
from oaTests.Managers.InstallationManager import InstallationManager

# Import Managers
from oaTests.Managers.MaintenanceManager import MaintenanceManager
from oaTests.Workers.collate_data import collate_extra_tabs
from oaTests.Workers.run_report_builder import ReportGenerator
from oaTests.Core.Workers import identify_test_directories

from .center_panel import CenterPanel
from .debug_matrix_screen import DebugMatrixScreen

# Import panel modules
from .left_panel import LeftPanel
from .maintenance_clear_screen import MaintenanceClearScreen
from .right_panel import RightPanel


class TestsApp(App):
    """A Textual app to manage the OPEN-AIR test suite."""

    CSS_PATH = None # CSS is inline for now as per original
    CSS = """
    Screen { background: #1e1e1e; }
    Header { background: #F4902C; color: #000000; text-style: bold; }
    #sidebar { width: 45; background: #2b2b2b; border-right: solid #F4902C; padding: 1; }
    #process-controls { height: 3; background: #2b2b2b; border-bottom: solid #F4902C; padding: 0 1; align: left middle; }
    #process-controls Label { margin-top: 1; }
    #process-controls Button { width: 25; margin: 0 1; }
    #stats-sidebar { width: 42; background: #2b2b2b; border-left: solid #F4902C; padding: 1; }
    #main-content { padding: 1; }
    .status-label { margin: 1 0; text-style: bold; color: #F4902C; }
    .status-item { margin-left: 2; color: #aaaaaa; }
    Button { width: 100%; margin: 1 0; }
    Button.-active { background: #F4902C; color: #000000; }
    #btn_report { background: #F4902C; color: #000000; text-style: bold; border: tall #000000; }
    #btn_report.flashing { background: #00ff00; color: #000000; }
    #btn_cancel_audits { display: none; }
    #btn_debug_on, #btn_debug_off, #btn_clear_logs, #btn_clear_audits, #btn_clear_reports, #btn_clear_jsonlines, #btn_clear_mqtt, #btn_clear_flame, #btn_clear_cache,
    #btn_deps, #btn_clean, #btn_infra, #btn_desktop, #btn_tests_install, #btn_full {
        background: #F4902C; color: #ff0000; text-style: bold;
    }
    #btn_debug_on:hover, #btn_debug_off:hover, #btn_clear_logs:hover, #btn_clear_audits:hover, #btn_clear_reports:hover, #btn_clear_jsonlines:hover, #btn_clear_mqtt:hover, #btn_clear_flame:hover, #btn_clear_cache:hover,
    #btn_deps:hover, #btn_clean:hover, #btn_infra:hover, #btn_desktop:hover, #btn_tests_install:hover, #btn_full:hover {
        background: #ff0000; color: #F4902C;
    }
    .violet-button {
        background: #8A2BE2;
        color: white;
        text-style: bold;
    }
    .violet-button:hover {
        background: #9400D3;
    }
    Log { background: #000000; border: solid #F4902C; height: 1fr; margin-top: 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "run_tests", "Run Tests"),
    ]

    def __init__(self, project_root):
        super().__init__()
        self.project_root = project_root
        self.stats_provider = SystemStatsProvider()
        self.log_lines = []
        self.test_results = []
        self.audit_cancel_event = threading.Event()
        self.summary = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
        self.mqtt_client = get_connection_manager()
        self.openair_process = None

        # Initialize Specialized Managers
        self.maintenance = MaintenanceManager(self.project_root, self.safe_write_log)
        self.installation = InstallationManager(self.project_root, self.safe_write_log)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield LeftPanel(id="sidebar")
            yield CenterPanel(id="main-content")
            yield RightPanel(id="stats-sidebar")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_stats)
        self.write_log("🚀 [READY] Test Suite initialized and standing by.")
        from oaConfigurationManager.FileReaders.config_reader import Config
        guid = Config.get_instance().INSTANCE_GUID
        self.query_one("#guid_label", Label).update(f"GUID: [bold #F4902C]{guid}[/]")
        self._start_ha_monitoring()

    def _start_ha_monitoring(self):
        def on_message(client, userdata, message):
            if "System/Failover/Status/" in message.topic:
                try:
                    data = message.get_json_payload()
                    role = data.get("role", "UNKNOWN")
                    from oaConfigurationManager.FileReaders.config_reader import Config
                    if data.get("guid") == Config.get_instance().INSTANCE_GUID:
                        color = "#00ff00" if role == "PRIMARY" else "#33A1FD"
                        self.call_from_thread(lambda: self.query_one("#role_label", Label).update(f"ROLE: [bold {color}]{role}[/]"))
                except Exception: pass
        self.mqtt_client.connect_to_broker(on_message_callback=on_message)
        self.mqtt_client.subscribe("OPEN-AIR/System/Failover/Status/#")

    def update_stats(self) -> None:
        stats = self.stats_provider.get_all_stats()
        self.query_one("#cpu_label", Label).update(f"⚡ CPU Speed: [bold #F4902C]{stats['cpu_mhz']:.0f} MHz[/]")
        self.query_one("#cores_label", Label).update(f"💻 CPU Cores: [bold #F4902C]{stats['cpu_cores']}[/]")
        self.query_one("#ram_label", Label).update(f"🧠 RAM Usage: [bold #F4902C]{stats['ram_percent']}%[/] ({stats['ram_used_gb']:.1f}/{stats['ram_total_gb']:.1f} GB)")
        self.query_one("#disk_label", Label).update(f"💿 Disk Free: [bold #F4902C]{stats['disk_free_gb']:.1f} GB[/] ({stats['disk_percent']:.1f}%)")

    def write_log(self, message: str) -> None:
        self.query_one(CenterPanel).log_widget.write_line(message)
        self.log_lines.append(message)
        TEST_LOGGER.info(message)

    def safe_write_log(self, message: str) -> None:
        """Thread-safe logging that works from both main and background threads."""
        if threading.get_ident() == getattr(self, "_thread_id", None):
            self.write_log(message)
        else:
            self.call_from_thread(self.write_log, message)

    def _start_report_flashing(self):
        if not hasattr(self, "_flash_timer"): self._flash_timer = self.set_interval(0.5, self._toggle_report_flash)

    def _toggle_report_flash(self): self.query_one("#btn_report").toggle_class("flashing")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        # OPEN-AIR Process
        if bid == "btn_start_oa": self.perform_start_openair()
        elif bid == "btn_stop_oa": self.perform_stop_openair()
        # Tests & Audits
        elif bid == "btn_unit": self.perform_unit_tests()
        elif bid == "btn_flame": self.perform_flame_graph()
        elif bid == "btn_audits": self.perform_audits()
        elif bid == "btn_cancel_audits": self.audit_cancel_event.set()
        elif bid == "btn_report": self.perform_report_generation()
        elif bid == "btn_doxygenizer": self.perform_doxygenizer()
        # Screens
        elif bid == "btn_debug_matrix": self.push_screen(DebugMatrixScreen())
        elif bid == "btn_clear_menu": self.push_screen(MaintenanceClearScreen(self.maintenance))
        elif bid == "btn_open_gui_editor": self.perform_launch_editor()
        # Maintenance (via Manager)
        elif bid == "btn_clear_logs": self.maintenance.clear_logs()
        elif bid == "btn_clear_audits": self.maintenance.clear_audits()
        elif bid == "btn_clear_reports": self.maintenance.clear_reports()
        elif bid == "btn_clear_jsonlines": self.maintenance.clear_jsonlines()
        elif bid == "btn_clear_mqtt": self.maintenance.clear_mqtt()
        elif bid == "btn_clear_flame": self.maintenance.clear_flamegraph()
        elif bid == "btn_clear_cache": self.maintenance.clear_cache()
        # Installation (via Manager)
        elif bid == "btn_deps": self.installation.perform_dep_check()
        elif bid == "btn_clean": self.installation.perform_clean_install()
        elif bid == "btn_infra": self.installation.perform_infra_setup()
        elif bid == "btn_desktop": self.installation.perform_desktop_setup()
        elif bid == "btn_tests_install": self.installation.perform_install_validation()
        elif bid == "btn_full": self.installation.perform_full_installation(lambda: self.log_lines)

    def perform_doxygenizer(self):
        self.write_log("📖 [DOXYGEN] Starting Doxygen generation...")
        def task():
            script_path = os.path.join(self.project_root, "oaTests", "Workers", "MakeDoxygen.py")
            if not os.path.exists(script_path):
                self.safe_write_log("❌ [ERROR] MakeDoxygen.py script not found.")
                return

            try:
                proc = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=self.project_root
                )
                for line in iter(proc.stdout.readline, ''):
                    self.safe_write_log(line.strip())
                proc.wait()
                if proc.returncode == 0:
                    self.safe_write_log("✅ [SUCCESS] Doxygen generation complete.")
                else:
                    self.safe_write_log(f"❌ [ERROR] Doxygen generation failed with return code {proc.returncode}.")
            except Exception as e:
                self.safe_write_log(f"💥 [CRITICAL] Failed to run Doxygen script: {e}")
        threading.Thread(target=task, daemon=True).start()

    def perform_launch_editor(self):
        self.write_log("🚀 [EDITOR] Launching standalone GUI Designer...")
        def task():
            try:
                import tkinter as tk
                root = tk.Tk()
                # Call launch_editor(root, is_standalone=True) so that the created root window is used as the visible editor window.
                launch_editor(root, is_standalone=True)
                root.mainloop()
            except Exception as e:
                self.safe_write_log(f"💥 [ERROR] Failed to launch editor: {e}")
        threading.Thread(target=task, daemon=True).start()

    def perform_start_openair(self):
        if self.openair_process and self.openair_process.poll() is None:
            self.write_log("⚠️ [ALREADY RUNNING] OPEN-AIR is already active.")
            return
        self.write_log("🚀 [LAUNCH] Starting main OPEN-AIR system...")
        oa_path = os.path.join(self.project_root, "openair.py")
        try:
            self.openair_process = subprocess.Popen([sys.executable, oa_path], cwd=self.project_root, preexec_fn=os.setsid)
            self.write_log(f"✅ [SUCCESS] OPEN-AIR started (PID: {self.openair_process.pid})")
        except Exception as e: self.write_log(f"💥 [ERROR] Failed to start OPEN-AIR: {e}")

    def perform_stop_openair(self):
        if not self.openair_process or self.openair_process.poll() is not None:
            self.write_log("ℹ️ [IDLE] OPEN-AIR is not currently running."); return
        self.write_log("🛑 [KILL] Terminating OPEN-AIR process tree...")
        try:
            os.killpg(os.getpgid(self.openair_process.pid), signal.SIGTERM)
            self.openair_process.wait(timeout=5)
            self.write_log("✨ [TERMINATED] OPEN-AIR has been stopped.")
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(self.openair_process.pid), signal.SIGKILL)
            self.write_log("⚠️ [FORCE] SIGKILL sent.")
        except Exception as e: self.write_log(f"💥 [ERROR] Error: {e}")
        finally: self.openair_process = None

    def perform_unit_tests(self):
        def task():
            self.call_from_thread(self._start_report_flashing)
            self.test_results = []; self.summary = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
            def record_result(test, status, message="", cause="", duration=0):
                self.summary["total"] += 1
                if status == "passed": self.summary["passed"] += 1
                elif status == "failed": self.summary["failed"] += 1
                elif status == "error": self.summary["errors"] += 1
                elif status == "skipped": self.summary["skipped"] += 1
                desc = test.shortDescription() or message or "No description provided."
                self.test_results.append({
                    "classname": str(test.__class__.__name__),
                    "name": str(test),
                    "status": status,
                    "description": desc,
                    "message": message,
                    "cause": cause,
                    "duration": f"{duration:.4f}s"
                })
                self.safe_write_log(f"   {'✅' if status == 'passed' else '❌'} {test}: [bold]{status}[/]")
            found_dirs = identify_test_directories(self.project_root)
            runner = TestRunner(record_result)
            runner.run(found_dirs, top_level_dir=self.project_root)
            self.safe_write_log(f"🏁 [COMPLETE] Tests finished. Passed: {self.summary['passed']}")
            # Trigger report generation automatically
            self.perform_report_generation()
        threading.Thread(target=task, daemon=True).start()

    def perform_flame_graph(self):
        def task():
            self.call_from_thread(self._start_report_flashing)
            self.safe_write_log("🔥 [FLAME] Initiating system-wide profiling...")
            flame_path = os.path.join(self.project_root, "oaTests", "Methods", "FlameGraph", "Entry.py")
            if os.path.exists(flame_path):
                try:
                    proc = subprocess.Popen(["python3", flame_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    out, error = proc.communicate()
                    if out:
                        self.safe_write_log(out.strip())
                    if error:
                        self.safe_write_log(f"⚠️ {error.strip()}")
                    self.safe_write_log("✨ [SUCCESS] Flame graph data captured.")
                except Exception as e:
                    self.safe_write_log(f"❌ [ERROR] Flame profiling failed: {e}")
            else:
                self.safe_write_log("❌ [ERROR] Script not found.")
        threading.Thread(target=task, daemon=True).start()

    def perform_audits(self):
        if not getattr(self, "_audit_confirm", False):
            self.write_log("🤔 [CONFIRM] Click 'RUN ALL AUDITS' again to proceed."); self._audit_confirm = True; return
        self.write_log("🕵️ [AUDIT] Starting all system audits...")
        def task():
            self.audit_cancel_event.clear(); self._audit_confirm = False
            try: run_all_audits(self.safe_write_log, self.audit_cancel_event)
            except Exception as e: self.safe_write_log(f"💥 [ERROR] Audit failure: {e}")
        threading.Thread(target=task, daemon=True).start()

    def perform_report_generation(self):
        self.write_log("📝 [REPORT] Generating unified intelligence reports...")
        def task():
            if hasattr(self, "_flash_timer"): self._flash_timer.stop(); del self._flash_timer
            self.call_from_thread(lambda: self.query_one("#btn_report").remove_class("flashing"))
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            from oaOchestration.Core.path_initializer import DATA_REPORTS_DIR
            reports_dir = str(DATA_REPORTS_DIR)
            os.makedirs(reports_dir, exist_ok=True)
            html_path = os.path.join(reports_dir, f'UnifiedReport_{timestamp}.html')
            json_path = os.path.join(reports_dir, f'UnifiedReport_{timestamp}.json')
            extra_tabs = collate_extra_tabs(self.project_root)
            generator = ReportGenerator(html_path, json_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            generator.generate_json(self.summary, self.test_results)
            doxygen_path = os.path.join(self.project_root, 'oaDocumentation', 'Doxygen', 'html', 'index.html')
            generator.generate_html(self.summary, self.test_results, extra_tabs, doxygen_path)
            self.safe_write_log(f"✅ [SUCCESS] Reports generated at: {html_path}")
            webbrowser.open('file://' + os.path.realpath(html_path))
        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    TestsApp(project_root).run()
