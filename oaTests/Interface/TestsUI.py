# Interface/TestsUI.py
# Author: Anthony Peter Kuzub
# Version: 20260323.2015.1
#
# Description: Textual UI for the OPEN-AIR testing and maintenance suite.

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Log, Label
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
import asyncio
import os
import webbrowser
from typing import Coroutine, Any
from datetime import datetime
import threading

# Import moved components
from oaTests.Workers.run_test import TestRunner
from oaTests.Workers.collate_data import collate_extra_tabs
from oaTests.Workers.run_report_builder import ReportGenerator
from oaTests.Workers import DiscoverTests
from oaTests.Workers.Clear_logs import cleanup_logs
from oaTests.Workers.ClearMQTT import MQTTSweeper
from oaTests.Workers.Clear_flamegraph import cleanup_flamegraph
from oaTests.Workers.Clear_audits import cleanup_audits
from oaTests.Workers.Clear_reports import cleanup_reports
from oaTests.Workers.Clear_cache import purge_cache
from oaTests.Managers.AuditRunner import run_all_audits
from oaTests.Methods.DebugToggler import force_debug_on, force_debug_off

from oaInstallation.Core.SystemStats import SystemStatsProvider

class TestsApp(App):
    """A Textual app to manage the OPEN-AIR test suite."""

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

    Button {
        width: 100%;
        margin: 1 0;
    }

    Button.-active {
        background: #F4902C;
        color: #000000;
    }

    #btn_report {
        background: #F4902C;
        color: #000000;
        text-style: bold;
        border: tall #000000;
    }

    #btn_report.flashing {
        background: #00ff00;
        color: #000000;
    }

    #btn_cancel_audits {
        display: none;
    }

    /* Maintenance Buttons: Orange with Red Text */
    #btn_debug_on, #btn_debug_off, #btn_clear_logs, #btn_clear_audits, #btn_clear_reports, #btn_clear_mqtt, #btn_clear_flame, #btn_clear_cache {
        background: #F4902C;
        color: #ff0000;
        text-style: bold;
    }

    #btn_debug_on:hover, #btn_debug_off:hover, #btn_clear_logs:hover, #btn_clear_audits:hover, #btn_clear_reports:hover, #btn_clear_mqtt:hover, #btn_clear_flame:hover, #btn_clear_cache:hover {
        background: #ff0000;
        color: #F4902C;
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
        Binding("r", "run_tests", "Run Tests"),
    ]

    def __init__(self, project_root):
        super().__init__()
        self.project_root = project_root
        self.stats_provider = SystemStatsProvider()
        self.log_lines = []
        self.test_results = []
        self.audit_cancel_event = asyncio.Event()
        self.summary = {
            "total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0
        }

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Test Controls", classes="status-label")
                yield Button("RUN UNIT TESTS", id="btn_unit", variant="primary")
                yield Button("RUN FLAME GRAPH", id="btn_flame", variant="primary")
                yield Button("RUN ALL AUDITS", id="btn_audits", variant="primary")
                yield Button("CANCEL AUDITS", id="btn_cancel_audits", variant="error")
                yield Button("GENERATE REPORT", id="btn_report", variant="success", disabled=False)
                
                yield Label("Maintenance (CLEAR)", classes="status-label")
                yield Button("CLEAR LOGS", id="btn_clear_logs", variant="warning")
                yield Button("CLEAR AUDITS", id="btn_clear_audits", variant="warning")
                yield Button("CLEAR REPORTS", id="btn_clear_reports", variant="warning")
                yield Button("CLEAR MQTT", id="btn_clear_mqtt", variant="warning")
                yield Button("CLEAR FLAMEGRAPH", id="btn_clear_flame", variant="warning")
                yield Button("DELETE CACHE", id="btn_clear_cache", variant="error")

                yield Label("Set Debug Flags", classes="status-label")
                with Horizontal():
                    yield Button("FORCE DEBUG ON", id="btn_debug_on", variant="warning")
                    yield Button("FORCE DEBUG OFF", id="btn_debug_off", variant="warning")

            with Vertical(id="main-content"):
                yield Label("Execution Log")
                self.installation_log = Log()
                yield self.installation_log

            with Vertical(id="stats-sidebar"):
                yield Label("System Metrics", classes="status-label")
                self.cpu_label = Label("CPU: -- MHz", classes="status-item")
                yield self.cpu_label
                self.cores_label = Label("Cores: --", classes="status-item")
                yield self.cores_label
                self.ram_label = Label("RAM: --%", classes="status-item")
                yield self.ram_label
                self.disk_label = Label("Disk: -- GB free", classes="status-item")
                yield self.disk_label

        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_stats)
        self.write_log("🚀 [READY] Test Suite initialized and standing by.")

    def update_stats(self) -> None:
        stats = self.stats_provider.get_all_stats()
        self.cpu_label.update(f"⚡ CPU Speed: [bold #F4902C]{stats['cpu_mhz']:.0f} MHz[/]")
        self.cores_label.update(f"💻 CPU Cores: [bold #F4902C]{stats['cpu_cores']}[/]")
        self.ram_label.update(f"🧠 RAM Usage: [bold #F4902C]{stats['ram_percent']}%[/] ({stats['ram_used_gb']:.1f}/{stats['ram_total_gb']:.1f} GB)")
        self.disk_label.update(f"💿 Disk Free: [bold #F4902C]{stats['disk_free_gb']:.1f} GB[/] ({stats['disk_percent']:.1f}%)")

    def write_log(self, message: str) -> None:
        self.installation_log.write_line(message)
        self.log_lines.append(message)

    def _start_report_flashing(self):
        if not hasattr(self, "_flash_timer"):
            self._flash_timer = self.set_interval(0.5, self._toggle_report_flash)

    def _toggle_report_flash(self):
        self.query_one("#btn_report").toggle_class("flashing")

    def run_in_daemon_thread(self, func, *args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_unit":
            self.perform_unit_tests()
        elif event.button.id == "btn_flame":
            self.run_in_daemon_thread(self.perform_flame_graph)
        elif event.button.id == "btn_audits":
            self.perform_audits()
        elif event.button.id == "btn_cancel_audits":
            self.cancel_audits()
        elif event.button.id == "btn_report":
            self.perform_report_generation()
        elif event.button.id == "btn_debug_on":
            self.perform_force_debug_on()
        elif event.button.id == "btn_debug_off":
            self.perform_force_debug_off()
        elif event.button.id == "btn_clear_logs":
            self.perform_clear_logs()
        elif event.button.id == "btn_clear_audits":
            self.perform_clear_audits()
        elif event.button.id == "btn_clear_reports":
            self.perform_clear_reports()
        elif event.button.id == "btn_clear_mqtt":
            self.perform_clear_mqtt()
        elif event.button.id == "btn_clear_flame":
            self.perform_clear_flamegraph()
        elif event.button.id == "btn_clear_cache":
            self.perform_clear_cache()

    def perform_unit_tests(self):
        self.write_log("🔬 [SCAN] Starting Deep Test Discovery...")
        def task():
            self.call_from_thread(self._start_report_flashing)
            self.test_results = []
            self.summary = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}

            def record_result(test, status, message="", cause="", duration=0):
                self.summary["total"] += 1
                if status == "passed": self.summary["passed"] += 1
                elif status == "failed": self.summary["failed"] += 1
                elif status == "error": self.summary["errors"] += 1
                elif status == "skipped": self.summary["skipped"] += 1
                
                description = getattr(test, "_testMethodDoc", "") or "No description provided."
                description = description.strip().replace("\n", "<br>")

                self.test_results.append({
                    "classname": test.__class__.__name__, "name": str(test), "status": status,
                    "message": message, "cause": cause, "description": description,
                    "duration": f"{duration:.4f}s"
                })
                emoji = "✅" if status == "passed" else "❌"
                self.call_from_thread(self.write_log, f"   {emoji} {test}: [bold]{status}[/]")

            found_dirs = DiscoverTests.identify_test_directories(self.project_root)
            self.call_from_thread(self.write_log, f"📂 Discovery identified {len(found_dirs)} test-containing root folders.")
            
            runner = TestRunner(record_result)
            runner.run([self.project_root], top_level_dir=self.project_root)
            
            self.call_from_thread(self.write_log, f"🏁 [COMPLETE] Tests finished. Passed: {self.summary['passed']}, Failed: {self.summary['failed']}")
        self.run_in_daemon_thread(task)

    def perform_flame_graph(self):
        self.call_from_thread(self._start_report_flashing)
        self.call_from_thread(self.write_log, "🔥 [FLAME] Initiating system-wide profiling...")
        flame_path = os.path.join(self.project_root, "oaTests", "Methods", "FlameGraph", "Entry.py")
        if os.path.exists(flame_path):
            import subprocess
            process = subprocess.Popen(
                ["python3", flame_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            if stdout: self.call_from_thread(self.write_log, stdout.strip())
            if stderr: self.call_from_thread(self.write_log, f"[red]{stderr.strip()}[/]")
            self.call_from_thread(self.write_log, "✨ [SUCCESS] Flame graph data captured.")
        else:
            self.call_from_thread(self.write_log, "❌ [ERROR] Flame graph entry script not found.")

    def perform_audits(self):
        if not hasattr(self, "_audit_confirm") or not self._audit_confirm:
            self.write_log("💰 [COST WARNING] System audits consume API tokens and take time.")
            self.write_log("🤔 [CONFIRM] Are you sure? Click 'RUN ALL AUDITS' again to proceed.")
            self._audit_confirm = True
            self.query_one("#btn_audits").label = "CONFIRM: RUN AUDITS"
            self.query_one("#btn_audits").variant = "warning"
            return
        
        self.write_log("🕵️ [AUDIT] Starting all system audits...")
        def task():
            self.call_from_thread(lambda: self.query_one("#btn_audits").set(label="RUN ALL AUDITS", variant="primary"))
            self.call_from_thread(lambda: self.query_one("#btn_cancel_audits").set_styles(display="block"))
            self.audit_cancel_event.clear()
            self._audit_confirm = False

            try:
                run_all_audits(lambda msg: self.call_from_thread(self.write_log, msg), self.audit_cancel_event)
                if self.audit_cancel_event.is_set():
                    self.call_from_thread(self.write_log, "🛑 [HALT] Audits were cancelled by the user.")
                else:
                    self.call_from_thread(self.write_log, "✨ [SUCCESS] All audits completed successfully.")
            except Exception as e:
                self.call_from_thread(self.write_log, f"💥 [ERROR] Audit engine failure: {e}")
            finally:
                self.call_from_thread(lambda: self.query_one("#btn_cancel_audits").set_styles(display="none"))
        self.run_in_daemon_thread(task)

    def cancel_audits(self):
        self.write_log("⚠️ [SIGNAL] Sending cancellation request to audit engine...")
        self.audit_cancel_event.set()

    def perform_report_generation(self):
        self.write_log("📝 [REPORT] Generating unified intelligence reports...")
        def task():
            if hasattr(self, "_flash_timer"):
                self._flash_timer.stop()
                del self._flash_timer
                self.call_from_thread(lambda: self.query_one("#btn_report").remove_class("flashing"))

            file_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            display_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            reports_dir = os.path.join(self.project_root, 'oaReports')
            os.makedirs(reports_dir, exist_ok=True)
            
            html_path = os.path.join(reports_dir, f'UnifiedReport_{file_timestamp}.html')
            json_path = os.path.join(reports_dir, f'UnifiedReport_{file_timestamp}.json')

            self.call_from_thread(self.write_log, "📊 Collating extra report data...")
            extra_tabs = collate_extra_tabs(self.project_root)
            
            generator = ReportGenerator(html_path, json_path, display_timestamp)
            generator.generate_json(self.summary, self.test_results)
            generator.generate_html(self.summary, self.test_results, extra_tabs)
            
            self.call_from_thread(self.write_log, f"✅ [SUCCESS] Reports generated at: {html_path}")
            webbrowser.open('file://' + os.path.realpath(html_path))
        self.run_in_daemon_thread(task)

    def perform_force_debug_on(self):
        btn_on = self.query_one("#btn_debug_on")
        btn_off = self.query_one("#btn_debug_off")

        # If the other button is in its confirm state, this button acts as CANCEL
        if getattr(self, "_debug_off_confirm", False):
            self._debug_off_confirm = False
            btn_on.label = "FORCE DEBUG ON"
            btn_off.label = "FORCE DEBUG OFF"
            btn_on.variant = "warning"
            btn_off.variant = "warning"
            self.write_log("ℹ️ Action cancelled.")
            return

        # Standard execution path
        if not getattr(self, "_debug_on_confirm", False):
            # Entering confirmation state
            self.write_log("🚨 [SYSTEM] PREPARING TO FORCE ALL DEBUG FLAGS ON!")
            self.write_log("🤔 [CONFIRM] This will scan and enable debug mode. Are you sure? Click again to proceed.")
            self._debug_on_confirm = True
            btn_on.label = "CONFIRM: FORCE ON"
            btn_off.label = "CANCEL"
            btn_on.variant = "success"
            btn_off.variant = "error"
            return

        # Executing the action after confirmation
        self._debug_on_confirm = False
        btn_on.label = "FORCE DEBUG ON"
        btn_off.label = "FORCE DEBUG OFF"
        btn_on.variant = "warning"
        btn_off.variant = "warning"
        self.write_log("🔼 [REWIRE] Forcing all debug gates to ON...")
        self.run_in_daemon_thread(force_debug_on, self.project_root, lambda msg: self.call_from_thread(self.write_log, msg))

    def perform_force_debug_off(self):
        btn_on = self.query_one("#btn_debug_on")
        btn_off = self.query_one("#btn_debug_off")

        # If the other button is in its confirm state, this button acts as CANCEL
        if getattr(self, "_debug_on_confirm", False):
            self._debug_on_confirm = False
            btn_on.label = "FORCE DEBUG ON"
            btn_off.label = "FORCE DEBUG OFF"
            btn_on.variant = "warning"
            btn_off.variant = "warning"
            self.write_log("ℹ️ Action cancelled.")
            return

        # Standard execution path
        if not getattr(self, "_debug_off_confirm", False):
            # Entering confirmation state
            self.write_log("🚨 [SYSTEM] PREPARING TO FORCE ALL DEBUG FLAGS OFF!")
            self.write_log("🤔 [CONFIRM] This will scan and disable debug mode. Are you sure? Click again to proceed.")
            self._debug_off_confirm = True
            btn_off.label = "CONFIRM: FORCE OFF"
            btn_on.label = "CANCEL"
            btn_off.variant = "success"
            btn_on.variant = "error"
            return

        # Executing the action after confirmation
        self._debug_off_confirm = False
        btn_on.label = "FORCE DEBUG ON"
        btn_off.label = "FORCE DEBUG OFF"
        btn_off.variant = "warning"
        btn_on.variant = "warning"
        self.write_log("🔽 [REWIRE] Forcing all debug gates to OFF...")
        self.run_in_daemon_thread(force_debug_off, self.project_root, lambda msg: self.call_from_thread(self.write_log, msg))

    def _cleanup_task(self, task_func, start_msg, end_msg, *args):
        self.write_log(start_msg)
        self.run_in_daemon_thread(lambda: (task_func(*args), self.call_from_thread(self.write_log, end_msg)))

    def perform_clear_logs(self):
        self._cleanup_task(cleanup_logs, "🧹 [CLEANUP] Purging all application logs...", "✨ [SUCCESS] Logs cleared.", None)

    def perform_clear_audits(self):
        self._cleanup_task(cleanup_audits, "🧹 [CLEANUP] Purging all system audit results...", "✨ [SUCCESS] Audits cleared.")

    def perform_clear_reports(self):
        self._cleanup_task(cleanup_reports, "🧹 [CLEANUP] Purging old reports (preserving latest)...", "✨ [SUCCESS] Report cleanup complete.")
        
    def perform_clear_mqtt(self):
        self.write_log("🧹 [CLEANUP] Wiping the MQTT topic tree...")
        def task():
            sweeper = MQTTSweeper("localhost", 1883, "OPEN-AIR")
            sweeper.sweep()
            self.call_from_thread(self.write_log, "✨ [SUCCESS] MQTT topic tree sanitized.")
        self.run_in_daemon_thread(task)

    def perform_clear_flamegraph(self):
        self._cleanup_task(cleanup_flamegraph, "🧹 [CLEANUP] Deleting flame graph artifacts...", "✨ [SUCCESS] Flame graph data purged.")

    def perform_clear_cache(self):
        self._cleanup_task(purge_cache, "🌪️ [PURGE] Nuking local cache and running state...", "✨ [SUCCESS] Cache purged and structure re-initialized.")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = TestsApp(project_root)
    app.run()
