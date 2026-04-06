# oaTests/Interface/maintenance_clear_screen.py
import os
import pathlib
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Button, Footer
from textual.containers import Container
from oaOchestration.Core.path_initializer import DATA_LOGS_DIR, GLOBAL_PROJECT_ROOT, DATA_REPORTS_DIR

class MaintenanceClearScreen(Screen):
    """A dedicated screen for system cleanup and maintenance operations with verification."""

    CSS = """
    MaintenanceClearScreen {
        align: center middle;
    }

    #dialog {
        width: 70;
        height: auto;
        background: #2b2b2b;
        border: thick #F4902C;
        padding: 1;
    }

    .clear-label {
        text-style: bold;
        color: #F4902C;
        margin-bottom: 1;
    }

    Button {
        width: 100%;
        margin: 0 0;
    }

    #btn_close {
        margin-top: 1;
        background: #F4902C;
        color: black;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("MAINTENANCE: CLEAR OPERATIONS (Verifying...)", id="header_label", classes="clear-label")
            
            yield Button("CLEAR LOGS (--)", id="btn_clear_logs", variant="warning")
            yield Button("CLEAR AUDITS (--)", id="btn_clear_audits", variant="warning")
            yield Button("CLEAR REPORTS (--)", id="btn_clear_reports", variant="warning")
            yield Button("CLEAR JSON LINES (--)", id="btn_clear_jsonlines", variant="warning")
            yield Button("CLEAR MQTT (--)", id="btn_clear_mqtt", variant="warning")
            yield Button("CLEAR FLAMEGRAPH (--)", id="btn_clear_flame", variant="warning")
            yield Button("DELETE CACHE (--)", id="btn_clear_cache", variant="error")
            
            yield Button("CLOSE & RETURN", id="btn_close", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        """Perform initial scan on launch."""
        self.refresh_all_counts()

    def _count_files(self, directory, pattern="*"):
        """Utility to count files in a directory."""
        path = pathlib.Path(directory)
        if not path.exists():
            return 0
        return len(list(path.glob(pattern)))

    def refresh_all_counts(self):
        """Scans all system regions and updates button labels."""
        # 1. Logs
        log_dir = pathlib.Path(DATA_LOGS_DIR) / "ApplicationRunLog"
        log_count = self._count_files(log_dir, "*.log")
        self._update_button("btn_clear_logs", "CLEAR LOGS", log_count)

        # 2. Audits
        audit_dir = pathlib.Path(DATA_LOGS_DIR) / "Audits"
        audit_count = self._count_files(audit_dir, "*")
        self._update_button("btn_clear_audits", "CLEAR AUDITS", audit_count)

        # 3. Reports
        report_dir = DATA_REPORTS_DIR
        report_count = self._count_files(report_dir, "*.html")
        # Keep 1 report usually, but for UI we show total
        self._update_button("btn_clear_reports", "CLEAR REPORTS", report_count)

        # 4. JSON Lines
        jsonl_dir = pathlib.Path(DATA_LOGS_DIR) / "JsonLines"
        jsonl_count = self._count_files(jsonl_dir, "*.jsonl")
        self._update_button("btn_clear_jsonlines", "CLEAR JSON LINES", jsonl_count)

        # 5. Flamegraph
        flame_dir = GLOBAL_PROJECT_ROOT / "oaTests" / "Methods" / "FlameGraph" / "output"
        flame_count = self._count_files(flame_dir, "*.html")
        self._update_button("btn_clear_flame", "CLEAR FLAMEGRAPH", flame_count)

        # 6. Cache
        cache_dir = GLOBAL_PROJECT_ROOT / "oaDataCache"
        cache_count = self._count_files(cache_dir, "*")
        self._update_button("btn_clear_cache", "DELETE CACHE", cache_count)

        # 7. MQTT (Placeholder for topic count if broker is reachable)
        self.query_one("#btn_clear_mqtt", Button).label = "CLEAR MQTT TOPICS"
        self.query_one("#header_label", Label).update("MAINTENANCE: CLEAR OPERATIONS")

    def _update_button(self, btn_id, base_label, count):
        btn = self.query_one(f"#{btn_id}", Button)
        btn.label = f"{base_label} ({count})"
        if count == 0:
            btn.variant = "success"
        else:
            # Revert to warning if files reappear
            if btn_id == "btn_clear_cache":
                btn.variant = "error"
            else:
                btn.variant = "warning"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_close":
            self.app.pop_screen()
        else:
            # Delegate the actual work back to the main app
            self.app.on_button_pressed(event)
            # Schedule a refresh after a short delay to allow file I/O to finish
            self.set_timer(1.0, self.refresh_all_counts)
