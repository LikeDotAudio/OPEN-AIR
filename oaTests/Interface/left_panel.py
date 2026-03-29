# oaTests/Interface/left_panel.py
from textual.widgets import Label, Button
from textual.containers import Vertical, Horizontal

class LeftPanel(Vertical):
    def compose(self):
        yield Label("System Identity", classes="status-label")
        yield Label("GUID: --", classes="status-item", id="guid_label")
        yield Label("ROLE: INITIALIZING", classes="status-item", id="role_label")

        yield Label("Installation Controls", classes="status-label")
        yield Button("RUN DEPENDENCY CHECK", id="btn_deps", variant="primary")
        yield Button("CLEAN INSTALLATION", id="btn_clean", variant="error")
        yield Button("SETUP MQTT/SNMP", id="btn_infra", variant="primary")
        yield Button("SETUP DESKTOP ICON", id="btn_desktop", variant="primary")
        yield Button("RUN VALIDATION TESTS", id="btn_tests_install", variant="primary")
        yield Button("FULL INSTALLATION", id="btn_full", variant="success")

        yield Label("Debug Flags", classes="status-label")


        yield Button("FORCE DEBUG ON", id="btn_debug_on", variant="warning")
        yield Button("FORCE DEBUG OFF", id="btn_debug_off", variant="warning")
        
        yield Label("System Metrics", classes="status-label")
        yield Label("CPU: -- MHz", classes="status-item", id="cpu_label")
        yield Label("Cores: --", classes="status-item", id="cores_label")
        yield Label("RAM: --%", classes="status-item", id="ram_label")
        yield Label("Disk: -- GB free", classes="status-item", id="disk_label")
