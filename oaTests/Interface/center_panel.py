# oaTests/Interface/center_panel.py
from textual.widgets import Label, Log, Button
from textual.containers import Vertical, Horizontal

class CenterPanel(Vertical):
    def compose(self):
        with Horizontal(id="process-controls"):
            yield Label("Process Controls: ", classes="status-label")
            yield Button("START OPEN-AIR", id="btn_start_oa", variant="success")
            yield Button("STOP OPEN-AIR", id="btn_stop_oa", variant="error")
            
        yield Label("Execution Log", classes="status-label")
        self.log_widget = Log()
        yield self.log_widget
