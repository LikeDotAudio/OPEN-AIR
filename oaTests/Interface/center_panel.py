# oaTests/Interface/center_panel.py
from textual.widgets import Label, Log
from textual.containers import Vertical

class CenterPanel(Vertical):
    def compose(self):
        yield Label("Execution Log", classes="status-label")
        self.log_widget = Log()
        yield self.log_widget
