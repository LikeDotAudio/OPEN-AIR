# oaTests/Interface/TestsUI.py
#
# High-fidelity Textual TUI for the OPEN-AIR testing and maintenance suite.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1630.1
#
# Description:
# This module implements the main Textual application for managing the 
# OPEN-AIR test suite, system audits, and maintenance utilities. It 
# follows the Partitioned Architecture by serving as the UI layer that 
# orchestrates various Core workers and Managers.
#
# Architectural Role:
# - UI Orchestrator: Bridges user interaction with background test workers.
# - System Monitor: Provides real-time metrics and HA role status via MQTT.
# - Maintenance Hub: Centralizes logs, cache, and audit cleanup tools.

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Log, Label, Checkbox
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
import os
import sys
import webbrowser
import time
import subprocess
import signal
from typing import Any
from datetime import datetime
import threading

# Import worker logic
from oaTests.Workers.TestRunner.TestRunner import TestRunner
from oaTests.Workers.collate_data import collate_extra_tabs
from oaTests.Workers.run_report_builder import ReportGenerator
from oaTests.Workers.TestRunner import DiscoverTests
from oaTests.Workers.CleanupApps.Clear_logs import cleanup_logs
from oaTests.Workers.CleanupApps.ClearMQTT import MQTTSweeper
from oaTests.Workers.CleanupApps.Clear_flamegraph import cleanup_flamegraph
from oaTests.Workers.CleanupApps.Clear_audits import cleanup_audits
from oaTests.Workers.CleanupApps.Clear_reports import cleanup_reports
from oaTests.Workers.CleanupApps.Clear_cache import purge_cache
from oaTests.Workers.CleanupApps.Clear_JsonLines import cleanup_jsonlines
from oaTests.Managers.AuditRunner import run_all_audits
from oaTests.Managers.configIniEditor.manager import ConfigIniEditor
import asyncio
import orjson
from oaComMQTT.Entry import get_connection_manager

from oaInstallation.Managers.Setup import (
    SetupManager, STAGE_PYTHON_DEPS, STAGE_MQTT_INFRA, 
    STAGE_SNMP_INFRA, STAGE_DESKTOP_INTEG
)
from oaInstallation.FileWriters.LogWriter import InstallationLogWriter
from oaInstallation.Tests.test_installation_validator import run_all_tests as run_installation_tests

from oaInstallation.Core.SystemStats import SystemStatsProvider

# Import panel modules
from .left_panel import LeftPanel
from .center_panel import CenterPanel
from .right_panel import RightPanel
from .debug_matrix_screen import DebugMatrixScreen
from .maintenance_clear_screen import MaintenanceClearScreen

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

    #process-controls {
        height: 3;
        background: #2b2b2b;
        border-bottom: solid #F4902C;
        padding: 0 1;
        align: left middle;
    }

    #process-controls Label {
        margin-top: 1;
    }

    #process-controls Button {
        width: 25;
        margin: 0 1;
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

    /* Maintenance & Installation Buttons: Orange with Red Text */
    #btn_debug_on, #btn_debug_off, #btn_clear_logs, #btn_clear_audits, #btn_clear_reports, #btn_clear_jsonlines, #btn_clear_mqtt, #btn_clear_flame, #btn_clear_cache,
    #btn_deps, #btn_clean, #btn_infra, #btn_desktop, #btn_tests_install, #btn_full {
        background: #F4902C;
        color: #ff0000;
        text-style: bold;
    }

    #btn_debug_on:hover, #btn_debug_off:hover, #btn_clear_logs:hover, #btn_clear_audits:hover, #btn_clear_reports:hover, #btn_clear_jsonlines:hover, #btn_clear_mqtt:hover, #btn_clear_flame:hover, #btn_clear_cache:hover,
    #btn_deps:hover, #btn_clean:hover, #btn_infra:hover, #btn_desktop:hover, #btn_tests_install:hover, #btn_full:hover {
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
        self.setup_manager = SetupManager(project_root=self.project_root)
        self.installation_log_writer = InstallationLogWriter()
        self.log_lines = []
        self.test_results = []
        self.audit_cancel_event = threading.Event()
        self.summary = {
            "total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0
        }
        self.mqtt_client = get_connection_manager()
        self.openair_process = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            # Swapping LeftPanel and RightPanel assignments to match desired layout:
            # Left sidebar (id="sidebar") should have Test Controls/Maintenance buttons (original RightPanel code, now in left_panel.py)
            yield LeftPanel(id="sidebar")
            # Center remains the log
            yield CenterPanel(id="main-content")
            # Right sidebar (id="stats-sidebar") should have Debug buttons and System Metrics (original LeftPanel code, now in right_panel.py)
            yield RightPanel(id="stats-sidebar")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_stats)
        self.write_log("🚀 [READY] Test Suite initialized and standing by.")
        
        # Initial UI Labels
        from oaConfiguration.FileReaders.config_reader import Config
        guid = Config.get_instance().INSTANCE_GUID
        self.query_one("#guid_label", Label).update(f"GUID: [bold #F4902C]{guid}[/]")
        
        # Monitor HA Status
        self._start_ha_monitoring()

    def _start_ha_monitoring(self):
        def on_msg(client, userdata, msg):
            if "System/Failover/Status/" in msg.topic:
                try:
                    data = msg.get_json_payload()
                    role = data.get("role", "UNKNOWN")
                    # Update role if it matches this instance
                    from oaConfiguration.FileReaders.config_reader import Config
                    if data.get("guid") == Config.get_instance().INSTANCE_GUID:
                        color = "#00ff00" if role == "PRIMARY" else "#33A1FD"
                        self.call_from_thread(
                            lambda: self.query_one("#role_label", Label).update(
                                f"ROLE: [bold {color}]{role}[/]"
                            )
                        )
                except Exception: pass

        self.mqtt_client.connect_to_broker(on_message_callback=on_msg)
        self.mqtt_client.subscribe("OPEN-AIR/System/Failover/Status/#")

    def update_stats(self) -> None:
        stats = self.stats_provider.get_all_stats()
        # Querying by ID, so it should find the widgets regardless of which panel instance they are in.
        # The LeftPanel class (now in right_panel.py) defines the system metric labels with IDs.
        # This LeftPanel code is now yielded as RightPanel(id="stats-sidebar").
        # The query_one("#cpu_label", Label) should find the widget if it's correctly composed.
        self.query_one("#cpu_label", Label).update(f"⚡ CPU Speed: [bold #F4902C]{stats['cpu_mhz']:.0f} MHz[/]")
        self.query_one("#cores_label", Label).update(f"💻 CPU Cores: [bold #F4902C]{stats['cpu_cores']}[/]")
        self.query_one("#ram_label", Label).update(f"🧠 RAM Usage: [bold #F4902C]{stats['ram_percent']}%[/] ({stats['ram_used_gb']:.1f}/{stats['ram_total_gb']:.1f} GB)")
        self.query_one("#disk_label", Label).update(f"💿 Disk Free: [bold #F4902C]{stats['disk_free_gb']:.1f} GB[/] ({stats['disk_percent']:.1f}%)")

    def write_log(self, message: str) -> None:
        center_panel = self.query_one(CenterPanel)
        center_panel.log_widget.write_line(message)
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
        if event.button.id == "btn_start_oa":
            self.perform_start_openair()
        elif event.button.id == "btn_stop_oa":
            self.perform_stop_openair()
        elif event.button.id == "btn_unit":
            self.perform_unit_tests()
        elif event.button.id == "btn_flame":
            self.run_in_daemon_thread(self.perform_flame_graph)
        elif event.button.id == "btn_audits":
            self.perform_audits()
        elif event.button.id == "btn_cancel_audits":
            self.cancel_audits()
        elif event.button.id == "btn_report":
            self.perform_report_generation()
        elif event.button.id == "btn_debug_matrix":
            self.push_screen(DebugMatrixScreen())
        elif event.button.id == "btn_clear_menu":
            self.push_screen(MaintenanceClearScreen())
        elif event.button.id == "btn_clear_logs":
            self.perform_clear_logs()
        elif event.button.id == "btn_clear_audits":
            self.perform_clear_audits()
        elif event.button.id == "btn_clear_reports":
            self.perform_clear_reports()
        elif event.button.id == "btn_clear_jsonlines":
            self.perform_clear_jsonlines()
        elif event.button.id == "btn_clear_mqtt":
            self.perform_clear_mqtt()
        elif event.button.id == "btn_clear_flame":
            self.perform_clear_flamegraph()
        elif event.button.id == "btn_clear_cache":
            self.perform_clear_cache()
        # Installation Handlers
        elif event.button.id == "btn_deps":
            self.run_in_daemon_thread(self.perform_dep_check)
        elif event.button.id == "btn_clean":
            self.run_in_daemon_thread(self.perform_clean_install)
        elif event.button.id == "btn_infra":
            self.run_in_daemon_thread(self.perform_infra_setup)
        elif event.button.id == "btn_desktop":
            self.run_in_daemon_thread(self.perform_desktop_setup)
        elif event.button.id == "btn_tests_install":
            self.run_in_daemon_thread(self.perform_install_validation)
        elif event.button.id == "btn_full":
            self.run_in_daemon_thread(self.perform_full_installation)

    def perform_start_openair(self):
        if self.openair_process and self.openair_process.poll() is None:
            self.write_log("⚠️ [ALREADY RUNNING] OPEN-AIR is already active.")
            return

        self.write_log("🚀 [LAUNCH] Starting main OPEN-AIR system...")
        oa_path = os.path.join(self.project_root, "openair.py")
        
        try:
            # Launch as a new process group so we can kill all children later
            self.openair_process = subprocess.Popen(
                [sys.executable, oa_path],
                cwd=self.project_root,
                preexec_fn=os.setsid
            )
            self.write_log(f"✅ [SUCCESS] OPEN-AIR started (PID: {self.openair_process.pid})")
        except Exception as e:
            self.write_log(f"💥 [ERROR] Failed to start OPEN-AIR: {e}")

    def perform_stop_openair(self):
        if not self.openair_process or self.openair_process.poll() is not None:
            self.write_log("ℹ️ [IDLE] OPEN-AIR is not currently running.")
            # Check for zombie processes just in case
            return

        self.write_log("🛑 [KILL] Terminating OPEN-AIR process tree...")
        try:
            # Kill the entire process group
            os.killpg(os.getpgid(self.openair_process.pid), signal.SIGTERM)
            self.openair_process.wait(timeout=5)
            self.write_log("✨ [TERMINATED] OPEN-AIR has been stopped.")
        except subprocess.TimeoutExpired:
            self.write_log("⚠️ [FORCE] Process group refused to exit. Sending SIGKILL...")
            os.killpg(os.getpgid(self.openair_process.pid), signal.SIGKILL)
        except Exception as e:
            self.write_log(f"💥 [ERROR] Error during shutdown: {e}")
        finally:
            self.openair_process = None

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
                description = description.strip()

                self.test_results.append({
                    "classname": test.__class__.__name__ if hasattr(test, "__class__") else "ManualTest", 
                    "name": str(test), "status": status,
                    "message": message, "cause": cause, "description": description,
                    "duration": f"{duration:.4f}s"
                })
                emoji = "✅" if status == "passed" else "❌"
                self.call_from_thread(self.write_log, f"   {emoji} {test}: [bold]{status}[/]")

            # 1. First Test: Dependency Check
            self.call_from_thread(self.write_log, "📦 [DEPS] Starting initial dependency validation...")
            start_deps = time.time()
            # Capture output from dependency check
            dep_logs = []
            def dep_callback(m): dep_logs.append(m)
            
            deps_success = self.setup_manager.check_dependencies(dep_callback, auto_install=False)
            dep_duration = time.time() - start_deps
            
            # Create a mock test object for the report
            class DependencyTest:
                def __init__(self):
                    self._testMethodDoc = "Validates all essential Python library requirements."
                def __str__(self): return "System Dependency Validation"
            
            record_result(
                DependencyTest(), 
                "passed" if deps_success else "failed", 
                message="Dependency check complete.",
                cause="\n".join(dep_logs) if not deps_success else "",
                duration=dep_duration
            )

            # 2. Continue with Discovered Tests
            found_dirs = DiscoverTests.identify_test_directories(self.project_root)
            self.call_from_thread(self.write_log, f"📂 Discovery identified {len(found_dirs)} test-containing root folders.")
            
            runner = TestRunner(record_result)
            runner.run(found_dirs, top_level_dir=self.project_root)
            
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
            def ui_pre_audit():
                btn = self.query_one("#btn_audits")
                btn.label = "RUN ALL AUDITS"
                btn.variant = "primary"
                self.query_one("#btn_cancel_audits").styles.display = "block"

            self.call_from_thread(ui_pre_audit)
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
                def ui_post_audit():
                    self.query_one("#btn_cancel_audits").styles.display = "none"
                self.call_from_thread(ui_post_audit)
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

    def _cleanup_task(self, task_func, start_msg, end_msg, *args):
        self.write_log(start_msg)
        self.run_in_daemon_thread(lambda: (task_func(*args), self.call_from_thread(self.write_log, end_msg)))

    def perform_clear_logs(self):
        self._cleanup_task(cleanup_logs, "🧹 [CLEANUP] Purging all application logs...", "✨ [SUCCESS] Logs cleared.", None)

    def perform_clear_audits(self):
        self._cleanup_task(cleanup_audits, "🧹 [CLEANUP] Purging all system audit results...", "✨ [SUCCESS] Audits cleared.")

    def perform_clear_reports(self):
        self._cleanup_task(cleanup_reports, "🧹 [CLEANUP] Purging old reports (preserving latest)...", "✨ [SUCCESS] Report cleanup complete.")

    def perform_clear_jsonlines(self):
        self._cleanup_task(cleanup_jsonlines, "🧹 [CLEANUP] Purging all JSON Lines logs...", "✨ [SUCCESS] JsonLines cleared.")
        
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

    # --- Installation Management Methods ---
    def perform_dep_check(self):
        def task():
            self.call_from_thread(self.write_log, "🕵️ [MISSION] Initiating deep scan for legendary dependencies...")
            
            # Use a wrapper for write_log to ensure it's called from the UI thread
            ui_write_log = lambda msg: self.call_from_thread(self.write_log, msg)
            
            # Logic from SetupUI.py adapted for Test UI
            # First check without auto-installing
            success = self.setup_manager.check_dependencies(ui_write_log, auto_install=False)
            
            if success:
                ui_write_log("🎆 [CELEBRATION] Every single package is in place! This environment is impeccable.")
            else:
                ui_write_log("😲 [SCANDAL] We are missing some essential components!")
                ui_write_log("🤔 [INQUIRY] Should I deploy the engineering team to install the missing pieces?")
                ui_write_log("💡 Tip: Click 'Run Dependency Check' again to attempt auto-repair.")
                
                # Check for second click (re-use SetupUI logic)
                if hasattr(self, "_dep_check_failed") and self._dep_check_failed:
                    ui_write_log("🏗️ [CONSTRUCTION] Engineering team deployed! Repairing the environment...")
                    success = self.setup_manager.check_dependencies(ui_write_log, auto_install=True)
                    if success:
                        ui_write_log("🏆 [TRIUMPH] Environment restored to its former glory!")
                    else:
                        ui_write_log("💀 [DISASTER] Even our best engineers couldn't fix this. Manual intervention required.")
                    self._dep_check_failed = False
                else:
                    self._dep_check_failed = True
        
        task()

    def perform_clean_install(self):
        def task():
            ui_write_log = lambda msg: self.call_from_thread(self.write_log, msg)
            
            if not hasattr(self, "_clean_confirm") or not self._clean_confirm:
                ui_write_log("🚨 [CRITICAL] YOU HAVE REQUESTED A CLEAN INSTALLATION!")
                ui_write_log("🛑 [WARNING] This will UNINSTALL and RE-INSTALL all elite packages.")
                ui_write_log("🤔 [CONFIRM] Are you absolutely sure? Click 'Clean Installation' again to proceed.")
                self._clean_confirm = True
                return

            self._clean_confirm = False
            ui_write_log("🌪️ [PURGE] Initiating full environmental scrub...")
            try:
                success = self.setup_manager.check_dependencies(ui_write_log, auto_install=True, clean_install=True)
                if success:
                    ui_write_log("✨ [POLISHED] All dependencies have been purged and perfectly re-installed!")
                else:
                    ui_write_log("💀 [FAILURE] The purge was successful, but the re-population failed!")
            except Exception as e:
                ui_write_log(f"💥 [CRITICAL ERROR] The scrub process crashed: {e}")

        task()

    def perform_infra_setup(self):
        def task():
            ui_write_log = lambda msg: self.call_from_thread(self.write_log, msg)
            ui_write_log("🚀 [MISSION] Provisioning world-class infrastructure...")
            
            mqtt_success = self.setup_manager.setup_mqtt(ui_write_log)
            snmp_success = self.setup_manager.setup_snmp(ui_write_log)
            
            if mqtt_success and snmp_success:
                ui_write_log("💎 [ELITE] Infrastructure is robust and ready for traffic.")
        
        task()

    def perform_desktop_setup(self):
        def task():
            ui_write_log = lambda msg: self.call_from_thread(self.write_log, msg)
            ui_write_log("🚀 [MISSION] Integrating with the master desktop environment...")
            success = self.setup_manager.setup_desktop(ui_write_log)
            if success:
                ui_write_log("🎨 [STYLISH] The OPEN-AIR icon is now a permanent fixture of your workspace.")
        
        task()

    def perform_install_validation(self):
        def task():
            ui_write_log = lambda msg: self.call_from_thread(self.write_log, msg)
            ui_write_log("🚀 [MISSION] Performing final high-stakes validation...")
            success = run_installation_tests(ui_write_log)
            if success:
                ui_write_log("🥇 [PRESTIGE] All systems have passed rigorous testing. We are GO for launch.")
            else:
                ui_write_log("⚠️ [ANOMALY] Validation failed! Minor adjustments may be needed.")
        
        task()

    def perform_full_installation(self):
        def task():
            ui_write_log = lambda msg: self.call_from_thread(self.write_log, msg)
            ui_write_log("🔥 [IGNITION] Starting FULL INSTALLATION process...")
            
            # Check dependencies
            success = self.setup_manager.check_dependencies(ui_write_log, auto_install=False)
            if not success:
                ui_write_log("🏗️ [CONSTRUCTION] Engineering team deployed! Repairing the environment...")
                success = self.setup_manager.check_dependencies(ui_write_log, auto_install=True)
            
            if success:
                mqtt_ok = self.setup_manager.setup_mqtt(ui_write_log)
                snmp_ok = self.setup_manager.setup_snmp(ui_write_log)
                if mqtt_ok and snmp_ok:
                    if self.setup_manager.setup_desktop(ui_write_log):
                        run_installation_tests(ui_write_log)
                        ui_write_log("🏆 [LEGENDARY] FULL INSTALLATION COMPLETE! The system is magnificent.")
                        
                        # Save the log
                        log_content = "\n".join(self.log_lines)
                        if self.installation_log_writer.write_log(log_content):
                            ui_write_log(f"💾 [SECURE] Log archived at: {self.installation_log_writer.get_log_path()}")
                    else:
                        ui_write_log("🛑 [HALT] Desktop integration failed.")
                else:
                    ui_write_log("🛑 [HALT] Infrastructure setup failed.")
            else:
                ui_write_log("🛑 [HALT] Dependency check failed. Aborting full install.")

        task()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = TestsApp(project_root)
    app.run()
