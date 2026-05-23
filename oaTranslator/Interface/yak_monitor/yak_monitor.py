import inspect
import pathlib
import sys
import tkinter as tk
from tkinter import ttk

import orjson

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
# Find project root (looking for GEMINI.md)
root_path = current_dir
for parent in current_dir.parents:
    if (parent / "GEMINI.md").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from oaLogging.Methods.matrix_gate import matrix_log
from oaStyle.Core.style import DEFAULT_THEME, THEMES
from oaTranslator.Managers.yak_trigger_handler import register_monitor_callback, unregister_monitor_callback

from .yak_dissector_pane import YakDissectorPane
from .yak_log_pane import YakLogPane


class YakMonitor(tk.Frame, SyncBehavior):
    """
    A GUI monitor that displays a running list of 'Yak' related MQTT messages,
    with a JSON dissector for inspecting payloads.
    """

    def __init__(self, parent, json_path=None, config=None, **kwargs):
        self.configuration = config or {}
        self.theme_colors = self.configuration.get("theme_colors", THEMES[DEFAULT_THEME])

        # Set default background to match theme for non-transparent areas
        if "bg" not in kwargs and "background" not in kwargs:
            kwargs["bg"] = self.theme_colors.get("bg", "#2b2b2b")

        super().__init__(parent, **kwargs)

        self._setup_styles()
        self._setup_ui()

        # --- Transparency Integration ---
        builder = self._find_builder_instance(parent)
        if builder:
            self._apply_transparency(self, canvas=None, configuration={}, builder_instance=builder)

        # Register for updates
        register_monitor_callback(self.on_yak_traffic)

        matrix_log("core", "system", inspect.currentframe().f_code.co_name, "🖥️ Yak Monitor Initialized.", "DEBUG")

    def _find_builder_instance(self, widget):
        """Recursively searches for a LoaderOrchestrator in the parent hierarchy."""
        from oaGui.Workers.orchestration.loader_orchestrator import LoaderOrchestrator
        curr = widget
        while curr:
            if isinstance(curr, LoaderOrchestrator):
                return curr
            try:
                curr = curr.master
            except Exception as e:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name, f"End of parent hierarchy reached for {widget}: {e}", "TRACE")
                break
        return None

    def _setup_styles(self):
        """Configures custom styles for the dark background."""
        style = ttk.Style()
        bg_color = self.theme_colors.get("bg", "#2b2b2b")

        style.configure("Dark.TFrame", background=bg_color)
        style.configure("Dark.TLabel", background=bg_color, foreground=self.theme_colors.get("fg", "#dcdcdc"))

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.main_frame = tk.Frame(self, bg=self.cget("bg"))
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(self.main_frame, text="Yak Traffic Monitor", font=("Helvetica", 12, "bold"), style="Dark.TLabel").pack(side=tk.TOP, pady=(0, 5))

        paned_window = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        self.log_pane = YakLogPane(paned_window, self.on_log_select)
        paned_window.add(self.log_pane, weight=1)

        self.dissector_pane = YakDissectorPane(paned_window, self.cget("bg"))
        paned_window.add(self.dissector_pane, weight=1)

        controls_frame = tk.Frame(self.main_frame, bg=self.cget("bg"))
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        ttk.Button(controls_frame, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Jump to Latest", command=self.jump_to_latest).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Jump to Latest 'value:'", command=self.jump_to_latest_val).pack(side=tk.LEFT, padx=5)

    def on_yak_traffic(self, topic, payload):
        """Callback received from the handler. Schedules GUI update on the main thread."""
        self.after(0, lambda: self._update_log(topic, payload))

    def _update_log(self, topic, payload):
        """Performs the actual GUI update for the log tree."""
        if "visibility" in topic:
            return

        # OPEN-AIR/Device Type/YAK/Model/YAK/Action/COMMAND
        topic_parts = topic.split('/')
        if len(topic_parts) < 6:
            return

        device_type = topic_parts[1]
        model = topic_parts[3]
        yak_id = topic_parts[4]
        action = topic_parts[5]
        command = "/".join(topic_parts[6:])

        val_display = "-"
        ui_tags = ()
        try:
            payload_data = orjson.loads(payload)
            if isinstance(payload_data, dict):
                if "value" in payload_data:
                    val_display = str(payload_data["value"])
                    ui_tags = ("green_row")
                elif "message" in payload_data:
                    val_display = payload_data["message"]
                    ui_tags = ("orange_row")
                elif "type" in payload_data:
                    val_display = f"[{payload_data['type']}]"
            elif "message" in payload:
                ui_tags = ("orange_row")
        except:
            if "message" in payload:
                ui_tags = ("orange_row")

        self.log_pane.add_entry((device_type, model, yak_id, action, command, val_display, payload), ui_tags)

    def on_log_select(self, event=None):
        """Handles selection in the log tree to populate the dissector."""
        selection = self.log_pane.tree.selection()
        if not selection:
            return

        values = self.log_pane.tree.item(selection[0], "values")
        if not values or len(values) < 7:
            return

        header_context = {
            "Device Type": values[0],
            "Model": values[1],
            "YAK": values[2],
            "Action": values[3],
            "Command": values[4]
        }
        raw_payload = values[6]
        self.dissector_pane.update(header_context, raw_payload)

    def jump_to_latest(self):
        """Jumps to the absolute latest message (top of the list)."""
        children = self.log_pane.tree.get_children()
        if children:
            self.log_pane.tree.selection_set(children[0])
            self.log_pane.tree.see(children[0])
            self.on_log_select()

    def jump_to_latest_val(self):
        """Finds the most recent log entry containing a 'value' key and selects it."""
        for item_id in self.log_pane.tree.get_children():
            item_values = self.log_pane.tree.item(item_id, "values")
            try:
                payload_json = orjson.loads(item_values[6])
                if isinstance(payload_json, dict) and "value" in payload_json:
                    self.log_pane.tree.selection_set(item_id)
                    self.log_pane.tree.see(item_id)
                    self.on_log_select()
                    return
            except:
                continue

    def clear_log(self):
        """Clears both the log pane and the dissector."""
        for item in self.log_pane.tree.get_children():
            self.log_pane.tree.delete(item)
        for item in self.dissector_pane.tree.get_children():
            self.dissector_pane.tree.delete(item)

    def render(self):
        """Required by SyncBehavior to sync background colors of children."""
        bg_color = self.cget("bg")
        self.main_frame.configure(bg=bg_color)
        if hasattr(self.dissector_pane, "header_frame"):
            self.dissector_pane.header_frame.configure(bg=bg_color)

    def destroy(self):
        unregister_monitor_callback(self.on_yak_traffic)
        super().destroy()

def get_gui_class():
    return YakMonitor
