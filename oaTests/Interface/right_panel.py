# oaTests/Interface/right_panel.py
from textual.widgets import Label, Button
from textual.containers import Vertical

class RightPanel(Vertical):
    def compose(self):
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
