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
        
        yield Label("System Maintenance", classes="status-label")
        yield Button("CLEAR MENU", id="btn_clear_menu", variant="warning")
        yield Button("OPEN GUI EDITOR", id="btn_open_gui_editor", classes="violet-button")
