# oaTests/Interface/left_panel.py
from textual.widgets import Label, Button
from textual.containers import Vertical, Horizontal

class LeftPanel(Vertical):
    def compose(self):
        yield Label("Debug Flags", classes="status-label")

        yield Button("FORCE DEBUG ON", id="btn_debug_on", variant="warning")
        yield Button("FORCE DEBUG OFF", id="btn_debug_off", variant="warning")
        
        yield Label("System Metrics", classes="status-label")
        yield Label("CPU: -- MHz", classes="status-item", id="cpu_label")
        yield Label("Cores: --", classes="status-item", id="cores_label")
        yield Label("RAM: --%", classes="status-item", id="ram_label")
        yield Label("Disk: -- GB free", classes="status-item", id="disk_label")
