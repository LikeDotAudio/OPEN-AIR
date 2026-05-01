import pathlib
import sys

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
# project_root/oaGui/Assets/Assets/right_50/bottom_90/2_monitors/22_Yak_Monitor/yak_monitor.py
# -> project_root is 7 levels up
root_path = current_dir.parents[6]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import inspect

# 22_Yak_Monitor/yak_monitor.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import orjson

from oaLogging.Methods.matrix_gate import matrix_log

# --- Path Guard: Ensure project root is in sys.path ---
current_path = Path(__file__).resolve()
root_path = current_path
for parent in current_path.parents:
    if (parent / "oaComBroker").exists() and (parent / "oaGui/Assets").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
    sys.path.append(str(root_path))


from oaGui.Workers.transparency.transparency_mixin import TransparencyMixin

# --- Protocol: Integration Layer ---
from oaStyle.Core.style import DEFAULT_THEME, THEMES
from oaTranslator.Managers.yak_trigger_handler import register_monitor_callback, unregister_monitor_callback


class YakMonitor(tk.Frame, TransparencyMixin):
    """
    A GUI monitor that displays a running list of 'Yak' related MQTT messages,
    with a JSON dissector for inspecting payloads.
    """

    def __init__(self, parent, json_path=None, config=None, **kwargs):
        self.config_data = config if config else {}
        self.theme_colors = self.config_data.get("theme_colors", THEMES[DEFAULT_THEME])

        # Set default background to match theme for non-transparent areas
        if "bg" not in kwargs and "background" not in kwargs:
            kwargs["bg"] = self.theme_colors.get("bg", "#2b2b2b")

        super().__init__(parent, **kwargs)

        self._setup_styles()
        self._setup_ui()

        # --- Transparency Integration ---
        builder = self._find_builder_instance(parent)
        if builder:
            self._apply_transparency(self, canvas=None, config_data={}, builder_instance=builder)

        # Register for updates
        register_monitor_callback(self.on_yak_traffic)

        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🖥️ Yak Monitor Initialized.", "DEBUG")

    def _find_builder_instance(self, widget):
        """Recursively searches for a DynamicGuiBuilder in the parent hierarchy."""
        from oaGui.Workers.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder):
                return curr
            try:
                curr = curr.master
            except Exception as e:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"End of parent hierarchy reached for {widget}: {e}", "TRACE")
                break
        return None

    def _setup_styles(self):
        """Configures custom styles for the dark background."""
        self.style = ttk.Style()
        bg_color = self.theme_colors.get("bg", "#2b2b2b")

        self.style.configure("Dark.TFrame", background=bg_color)
        self.style.configure("Dark.TLabel", background=bg_color, foreground=self.theme_colors.get("fg", "#dcdcdc"))

class YakLogPane(ttk.Frame):
    """Encapsulates the traffic log treeview and its controls."""
    def __init__(self, parent, on_select_callback, **kwargs):
        super().__init__(parent, style="Dark.TFrame", **kwargs)
        self._on_select = on_select_callback
        self._setup_ui()

    def _setup_ui(self):
        cols = ("Device Type", "Model", "YAK", "Action", "Command", "Value", "Message")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            w = 400 if col == "Message" else (80 if col == "Value" else 100)
            self.tree.column(col, width=w, anchor="w" if col in ["Message", "Command", "Device Type", "Model", "YAK", "Action"] else "center")
        
        sy, sx = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview), ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky="nsew"); sy.grid(row=0, column=1, sticky="ns"); sx.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure("green_row", foreground="#00ff00"); self.tree.tag_configure("orange_row", foreground="#ffaa00")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def add_entry(self, values, tags):
        self.tree.insert("", 0, values=values, tags=tags)
        if len(self.tree.get_children()) > 1000: self.tree.delete(self.tree.get_children()[-1])

class YakDissectorPane(ttk.Frame):
    """Encapsulates the JSON deep packet inspection tree."""
    def __init__(self, parent, theme_bg, **kwargs):
        super().__init__(parent, style="Dark.TFrame", **kwargs)
        self.theme_bg = theme_bg
        self._setup_ui()

    def _setup_ui(self):
        self._setup_header()
        self.tree = ttk.Treeview(self, columns=("Value"), show="tree headings")
        self.tree.heading("#0", text="Key / Index"); self.tree.heading("Value", text="Value")
        self.tree.column("#0", width=200, anchor="w"); self.tree.column("Value", width=400, anchor="w")
        sy = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); sy.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_header(self):
        f = tk.Frame(self, bg=self.theme_bg); f.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))
        self.vars = {k: tk.StringVar(value=f"{k}: -") for k in ["Device Type", "Model", "YAK", "Action", "Command"]}
        d = tk.Frame(f, bg=self.theme_bg); d.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for k in self.vars: ttk.Label(d, textvariable=self.vars[k], font=("Helvetica", 10, "bold"), style="Dark.TLabel", padding=(0, 0, 10, 0)).pack(side=tk.LEFT)

    def update(self, details, payload):
        for k, v in details.items(): self.vars[k].set(f"{k}: {v}")
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            data = orjson.loads(payload)
            self._populate("", data)
        except: self.tree.insert("", "end", text="Raw Payload", values=(payload))

    def _populate(self, parent, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)): self._populate(self.tree.insert(parent, "end", text=k, open=True), v)
                else: self.tree.insert(parent, "end", text=k, values=(v))
        elif isinstance(data, list):
            for i, v in enumerate(data):
                if isinstance(v, (dict, list)): self._populate(self.tree.insert(parent, "end", text=f"[{i}]", open=True), v)
                else: self.tree.insert(parent, "end", text=f"[{i}]", values=(v))

class YakMonitor(tk.Frame, TransparencyMixin):
    """A GUI monitor that displays a running list of 'Yak' related MQTT messages."""
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        self.config_data = config or {}
        self.theme_colors = self.config_data.get("theme_colors", THEMES[DEFAULT_THEME])
        if "bg" not in kwargs: kwargs["bg"] = self.theme_colors.get("bg", "#2b2b2b")
        super().__init__(parent, **kwargs)
        self._setup_styles(); self._setup_ui()
        builder = self._find_builder_instance(parent)
        if builder: self._apply_transparency(self, canvas=None, config_data={}, builder_instance=builder)
        register_monitor_callback(self.on_yak_traffic)

    def _setup_styles(self):
        s, bg = ttk.Style(), self.theme_colors.get("bg", "#2b2b2b")
        s.configure("Dark.TFrame", background=bg); s.configure("Dark.TLabel", background=bg, foreground=self.theme_colors.get("fg", "#dcdcdc"))

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.main_frame = tk.Frame(self, bg=self.cget("bg")); self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(self.main_frame, text="Yak Traffic Monitor", font=("Helvetica", 12, "bold"), style="Dark.TLabel").pack(side=tk.TOP, pady=(0, 5))
        p = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL); p.pack(fill=tk.BOTH, expand=True)
        self.log_pane = YakLogPane(p, self.on_log_select); p.add(self.log_pane, weight=1)
        self.dissector_pane = YakDissectorPane(p, self.cget("bg")); p.add(self.dissector_pane, weight=1)
        
        ctrls = tk.Frame(self.main_frame, bg=self.cget("bg")); ctrls.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        ttk.Button(ctrls, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrls, text="Jump to Latest", command=self.jump_to_latest).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrls, text="Jump to Latest 'value:'", command=self.jump_to_latest_val).pack(side=tk.LEFT, padx=5)

    def on_yak_traffic(self, topic, payload):
        self.after(0, lambda: self._update_log(topic, payload))

    def _update_log(self, topic, payload):
        if "visibility" in topic: return
        p = topic.split('/')
        if len(p) < 6: return
        d_type, model, yak, action, cmd = p[1], p[3], p[4], p[5], "/".join(p[6:])
        val, tags = "-", ()
        try:
            data = orjson.loads(payload)
            if isinstance(data, dict):
                if "value" in data: val, tags = str(data["value"]), ("green_row")
                elif "message" in data: val, tags = data["message"], ("orange_row")
                elif "type" in data: val = f"[{data['type']}]"
            elif "message" in payload: tags = ("orange_row")
        except: 
            if "message" in payload: tags = ("orange_row")
        self.log_pane.add_entry((d_type, model, yak, action, cmd, val, payload), tags)

    def on_log_select(self, event=None):
        sel = self.log_pane.tree.selection()
        if not sel: return
        v = self.log_pane.tree.item(sel[0], "values")
        if not v or len(v) < 7: return
        self.dissector_pane.update({"Device Type": v[0], "Model": v[1], "YAK": v[2], "Action": v[3], "Command": v[4]}, v[6])

    def jump_to_latest(self):
        c = self.log_pane.tree.get_children()
        if c: self.log_pane.tree.selection_set(c[0]); self.log_pane.tree.see(c[0]); self.on_log_select()

    def jump_to_latest_val(self):
        for i in self.log_pane.tree.get_children():
            v = self.log_pane.tree.item(i, "values")
            try:
                if isinstance(orjson.loads(v[6]), dict) and "value" in orjson.loads(v[6]):
                    self.log_pane.tree.selection_set(i); self.log_pane.tree.see(i); self.on_log_select(); return
            except: continue

    def clear_log(self):
        for i in self.log_pane.tree.get_children(): self.log_pane.tree.delete(i)
        for i in self.dissector_pane.tree.get_children(): self.dissector_pane.tree.delete(i)

    def _find_builder_instance(self, widget):
        from oaGui.Workers.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder): return curr
            try: curr = curr.master
            except: break
        return None

    def render(self): self.main_frame.configure(bg=self.cget("bg"))

    def destroy(self): unregister_monitor_callback(self.on_yak_traffic); super().destroy()

    def _on_gui_visible(self, event=None):
        """Called when the tab becomes visible. Forces a reslice."""
        if hasattr(self, "_reslice_scheduled"):
            builder = self._find_builder_instance(self.master)
            if builder and hasattr(builder, "_trigger_reslice_all"):
                builder._trigger_reslice_all()

    def on_yak_traffic(self, topic, payload):
        """Callback received from the handler. Schedules GUI update on the main thread."""
        self.after(0, lambda: self._update_log(topic, payload))

    def _update_log(self, topic, payload):
        """Performs the actual GUI update for the log tree."""
        # Filter out visibility topics
        if "visibility" in topic:
            return

        # Parse Topic: OPEN-AIR/Device Type/YAK/Model/YAK/Action/COMMAND
        parts = topic.split('/')

        device_type = parts[1] if len(parts) > 1 else "-"
        # Index 2 is 'YAK' -> Skip
        model = parts[3] if len(parts) > 3 else "-"
        yak = parts[4] if len(parts) > 4 else "-"
        action = parts[5] if len(parts) > 5 else "-"
        command = "/".join(parts[6:]) if len(parts) > 6 else "-"

        # ⚡ EXTRACT VALUE
        val_display = "-"
        tags = ()
        try:
            data = orjson.loads(payload)
            if isinstance(data, dict):
                if "value" in data:
                    val_display = str(data["value"])
                    tags = ("green_row")
                elif "message" in data:
                    val_display = data["message"]
                    tags = ("orange_row")
                elif "type" in data:
                    val_display = f"[{data['type']}]"
            elif "message" in payload:
                tags = ("orange_row")
        except Exception as e:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Payload not JSON or error parsing for topic {topic}: {e}", "DEBUG")
            if "message" in payload:
                tags = ("orange_row")

        # Insert at the top
        self.log_tree.insert("", 0, values=(device_type, model, yak, action, command, val_display, payload), tags=tags)

        # Optional: Limit buffer size
        if len(self.log_tree.get_children()) > 1000:
            last_item = self.log_tree.get_children()[-1]
            self.log_tree.delete(last_item)

    def on_log_select(self, event=None):
        """Handles selection in the log tree to populate the dissector."""
        selected_items = self.log_tree.selection()
        if not selected_items:
            return

        # Clear dissector
        for item in self.dissector_tree.get_children():
            self.dissector_tree.delete(item)

        item_id = selected_items[0]
        values = self.log_tree.item(item_id, "values")

        if not values or len(values) < 7:
            return

        # Update Header Labels
        self.selected_topic_vars["Device Type"].set(f"Type: {values[0]}")
        self.selected_topic_vars["Model"].set(f"Model: {values[1]}")
        self.selected_topic_vars["YAK"].set(f"YAK: {values[2]}")
        self.selected_topic_vars["Action"].set(f"Action: {values[3]}")
        self.selected_topic_vars["Command"].set(f"Cmd: {values[4]}")

        payload = values[6] # Message is now the 7th column (index 6)

        try:
            data = orjson.loads(payload)
            self._populate_dissector("", data)
        except Exception as e:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Selected payload not JSON or error parsing: {e}", "DEBUG")
            # Not JSON or error parsing, show as raw string
            self.dissector_tree.insert("", "end", text="Raw Payload", values=(payload))

    def jump_to_latest_message(self):
        """Jumps to the absolute latest message (top of the list)."""
        children = self.log_tree.get_children()
        if children:
            item_id = children[0]
            self.log_tree.selection_set(item_id)
            self.log_tree.see(item_id)
            self.log_tree.focus(item_id)
            self.on_log_select()

    def jump_to_latest_val_message(self):
        """Finds the most recent log entry containing a 'value' key and selects it."""
        for item_id in self.log_tree.get_children():
            values = self.log_tree.item(item_id, "values")
            if values and len(values) >= 7:
                payload = values[6]
                try:
                    data = orjson.loads(payload)
                    if isinstance(data, dict) and "value" in data:
                        # Select and focus
                        self.log_tree.selection_set(item_id)
                        self.log_tree.see(item_id)
                        self.log_tree.focus(item_id)
                        # Trigger dissector update
                        self.on_log_select()
                        return
                except Exception as e:
                    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Skipping log entry in jump_to_latest_val_message: {e}", "TRACE")
                    continue

    def _populate_dissector(self, parent, data):
        """Recursively populates the dissector tree."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    node = self.dissector_tree.insert(parent, "end", text=key, open=True)
                    self._populate_dissector(node, value)
                else:
                    self.dissector_tree.insert(parent, "end", text=key, values=(value))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    node = self.dissector_tree.insert(parent, "end", text=f"[{i}]", open=True)
                    self._populate_dissector(node, item)
                else:
                    self.dissector_tree.insert(parent, "end", text=f"[{i}]", values=(item))

    def clear_log(self):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        for item in self.dissector_tree.get_children():
            self.dissector_tree.delete(item)

    def render(self):
        """Required by TransparencyMixin to sync background colors of children."""
        bg = self.cget("bg")
        self.main_frame.configure(bg=bg)
        self.dissect_header_frame.configure(bg=bg)

    def destroy(self):
        # Cleanup
        unregister_monitor_callback(self.on_yak_traffic)
        super().destroy()
