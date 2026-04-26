# oaTests/Interface/debug_matrix_screen.py
from textual.app import ComposeResult
from textual.containers import Container, Grid, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Label

from oaTests.Managers.configIniEditor.manager import ConfigIniEditor


class DebugMatrixScreen(Screen):
    """A dedicated screen for configuring the Hierarchical Debug Matrix."""

    CSS = """
    DebugMatrixScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: 45;
        background: #2b2b2b;
        border: thick #F4902C;
        padding: 1;
    }

    .matrix-label {
        text-style: bold;
        color: #F4902C;
        margin-bottom: 1;
        text-align: center;
    }

    .section-label {
        text-style: bold underline;
        color: #F4902C;
        margin-top: 1;
        margin-bottom: 1;
    }

    .matrix-item {
        margin-left: 2;
        color: #aaaaaa;
        text-style: bold italic;
        margin-top: 1;
    }

    .matrix-grid {
        grid-size: 2;
        grid-gutter: 1;
        height: auto;
        padding-left: 2;
    }

    #btn_close {
        margin-top: 1;
        background: #F4902C;
        color: black;
        width: 100%;
    }

    Checkbox {
        color: #e74c3c; /* Bright Red for False */
        background: transparent;
        width: 100%;
    }

    Checkbox.-on {
        color: #2ecc71; /* Bright Green for True */
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        editor = ConfigIniEditor()
        setup = editor.get_all_debug_sections()

        with Container(id="dialog"):
            yield Label("SYSTEM CONFIGURATION & DEBUG MATRIX", classes="matrix-label")

            with ScrollableContainer():
                # 1. Global Debug Section
                yield Label("GLOBAL DEBUG SETTINGS [Debug]", classes="section-label")
                with Grid(classes="matrix-grid"):
                    for key, value in setup["debug"].items():
                        chk_id = f"chk_dbg_{key.lower()}"
                        yield Checkbox(f"{key.upper().replace('_', ' ')}", value=value, id=chk_id)

                # 2. Matrix Master Switch
                yield Label("DEBUG MATRIX CONTROL", classes="section-label")
                yield Checkbox("MASTER MATRIX ENABLE", value=setup["master"], id="chk_master_debug")

                # 3. Systems
                yield Label("Systems", classes="matrix-item")
                with Grid(classes="matrix-grid"):
                    for sys_name, value in setup["systems"].items():
                        chk_id = f"chk_sys_{sys_name.lower()}"
                        yield Checkbox(f"{sys_name}", value=value, id=chk_id)

                # 4. Elements
                yield Label("Elements", classes="matrix-item")
                with Grid(classes="matrix-grid"):
                    for el_name, value in setup["elements"].items():
                        chk_id = f"chk_el_{el_name.lower()}"
                        yield Checkbox(f"{el_name}", value=value, id=chk_id)

            yield Button("CLOSE & RETURN", id="btn_close", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_close":
            self.app.pop_screen()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handles debug flag toggles by updating config.ini."""
        cid = event.checkbox.id
        if not cid: return

        editor = ConfigIniEditor()

        # Handle [Debug] section
        if cid.startswith("chk_dbg_"):
            config_key = cid.replace("chk_dbg_", "")
            editor.set_config_flag("Debug", config_key, event.value)
            return

        # Handle [DEBUG_MATRIX] section
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
            "chk_el_aes70": "element_aes70",
            "chk_el_rest": "element_rest",
            "chk_el_builder": "element_gui_builder"
        }

        if cid in key_map:
            config_key = key_map[cid]
            editor.set_debug_flag(config_key, event.value)
