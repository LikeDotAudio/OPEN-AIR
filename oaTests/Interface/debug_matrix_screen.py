# oaTests/Interface/debug_matrix_screen.py
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Checkbox, Button, Footer
from textual.containers import Vertical, Container
from oaTests.Managers.configIniEditor.manager import ConfigIniEditor

class DebugMatrixScreen(Screen):
    """A dedicated screen for configuring the Hierarchical Debug Matrix."""

    CSS = """
    DebugMatrixScreen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
        background: #2b2b2b;
        border: thick #F4902C;
        padding: 1;
    }

    .matrix-label {
        text-style: bold;
        color: #F4902C;
        margin-bottom: 1;
    }

    .matrix-item {
        margin-left: 2;
        color: #aaaaaa;
    }

    #btn_close {
        margin-top: 1;
        background: #F4902C;
        color: black;
    }

    Checkbox {
        color: #e74c3c; /* Bright Red for False */
        background: transparent;
    }

    Checkbox.-on {
        color: #2ecc71; /* Bright Green for True */
        text-style: bold;
    }

    Checkbox > .checkbox--toggle {
        /* [X] or [ ] will automatically follow the parent color in Textual */
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        editor = ConfigIniEditor()
        setup = editor.get_all_debug_sections()

        with Container(id="dialog"):
            yield Label("DEBUG MATRIX CONFIGURATION", classes="matrix-label")
            
            # 1. Master Switch
            yield Checkbox("MASTER DEBUG ENABLE", value=setup["master"], id="chk_master_debug")
            
            # 2. Systems
            yield Label("  [u]Systems[/]", classes="matrix-item")
            for sys_name, val in setup["systems"].items():
                chk_id = f"chk_sys_{sys_name.lower()}"
                yield Checkbox(f"  {sys_name}", value=val, id=chk_id)

            # 3. Elements
            yield Label("  [u]Elements[/]", classes="matrix-item")
            for el_name, val in setup["elements"].items():
                chk_id = f"chk_el_{el_name.lower()}"
                yield Checkbox(f"  {el_name}", value=val, id=chk_id)
            
            yield Button("CLOSE & RETURN", id="btn_close", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_close":
            self.app.pop_screen()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handles debug flag toggles by updating config.ini."""
        cid = event.checkbox.id
        if not cid: return
        
        # Map UI ID back to config.ini key
        key_map = {
            "chk_master_debug": "master_debug_enable",
            "chk_sys_comms": "sys_comms",
            "chk_sys_gui": "sys_gui",
            "chk_sys_data": "sys_data",
            "chk_sys_router": "sys_router",
            "chk_sys_core": "sys_core",
            "chk_el_mqtt": "element_mqtt",
            "chk_el_snmp": "element_snmp",
            "chk_el_midi": "element_midi",
            "chk_el_osc": "element_osc",
            "chk_el_builder": "element_gui_builder"
        }
        
        if cid in key_map:
            config_key = key_map[cid]
            editor = ConfigIniEditor()
            if editor.set_debug_flag(config_key, event.value):
                # We can't easily write to the main app log from here without 
                # custom events, but the change is saved to disk.
                pass
