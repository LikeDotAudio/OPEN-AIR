import os
import sys
import pathlib

# 1. Setup Environment
current_dir = pathlib.Path(__file__).resolve().parent
# project_root/oaGuiDefinitions/Assets/right_50/bottom_90/2_monitors/22_Yak_Monitor/yak_monitor.py
# -> project_root is 7 levels up
root_path = current_dir.parents[6]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# 22_Yak_Monitor/yak_monitor.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
import datetime
import orjson
from pathlib import Path

# --- Path Guard: Ensure project root is in sys.path ---
current_path = Path(__file__).resolve()
root_path = current_path
for parent in current_path.parents:
    if (parent / "oaComBroker").exists() and (parent / "oaGuiDefinitions").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
from oaTranslator.Managers.yak_trigger_handler import register_monitor_callback, unregister_monitor_callback

# --- Protocol: Integration Layer ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config

from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


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
        from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
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

    def _setup_ui(self):
        """Sets up the split-view UI."""
        self.pack(fill=tk.BOTH, expand=True)
        
        # Main container (Use tk.Frame for background inheritance)
        self.main_frame = tk.Frame(self, bg=self.cget("bg"))
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Header
        lbl = ttk.Label(self.main_frame, text="Yak Traffic Monitor", font=("Helvetica", 12, "bold"), style="Dark.TLabel")
        lbl.pack(side=tk.TOP, pady=(0, 5))
        
        # Paned Window (Splitter)
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # --- TOP PANE: Log ---
        self.log_frame = ttk.Frame(self.paned_window, style="Dark.TFrame")
        self.paned_window.add(self.log_frame, weight=1)
        
        # Updated Columns: Device Type, Model, YAK, Action, Command, Value, Message
        cols = ("Device Type", "Model", "YAK", "Action", "Command", "Value", "Message")
        self.log_tree = ttk.Treeview(self.log_frame, columns=cols, show="headings")
        
        for col in cols:
            self.log_tree.heading(col, text=col)
            if col == "Message":
                self.log_tree.column(col, width=400, anchor="w")
            elif col == "Value":
                self.log_tree.column(col, width=80, anchor="center")
            else:
                self.log_tree.column(col, width=100, anchor="w")
        
        self.log_scroll_y = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_scroll_x = ttk.Scrollbar(self.log_frame, orient=tk.HORIZONTAL, command=self.log_tree.xview)
        
        self.log_tree.configure(yscrollcommand=self.log_scroll_y.set, xscrollcommand=self.log_scroll_x.set)
        
        self.log_tree.grid(row=0, column=0, sticky="nsew")
        self.log_scroll_y.grid(row=0, column=1, sticky="ns")
        self.log_scroll_x.grid(row=1, column=0, sticky="ew")
        
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        # Configure Tags for Syntax Highlighting
        self.log_tree.tag_configure("green_row", foreground="#00ff00")  # Bright Green
        self.log_tree.tag_configure("orange_row", foreground="#ffaa00") # Bright Orange

        # Bind Selection
        self.log_tree.bind("<<TreeviewSelect>>", self.on_log_select)

        # --- BOTTOM PANE: Dissector ---
        self.dissector_frame = ttk.Frame(self.paned_window, style="Dark.TFrame")
        self.paned_window.add(self.dissector_frame, weight=1)
        
        self.dissect_header_frame = tk.Frame(self.dissector_frame, bg=self.cget("bg"))
        self.dissect_header_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))

        # Labels for Selected Message Details
        self.selected_topic_vars = {
            "Device Type": tk.StringVar(value="Type: -"),
            "Model": tk.StringVar(value="Model: -"),
            "YAK": tk.StringVar(value="YAK: -"),
            "Action": tk.StringVar(value="Action: -"),
            "Command": tk.StringVar(value="Cmd: -")
        }
        
        details_frame = tk.Frame(self.dissect_header_frame, bg=self.cget("bg"))
        details_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        for key in ["Device Type", "Model", "YAK", "Action", "Command"]:
            lbl = ttk.Label(details_frame, textvariable=self.selected_topic_vars[key], 
                            font=("Helvetica", 10, "bold"), style="Dark.TLabel", padding=(0, 0, 10, 0))
            lbl.pack(side=tk.LEFT)

        self.btn_jump_latest = ttk.Button(self.dissect_header_frame, text="Jump to Latest", command=self.jump_to_latest_message)
        self.btn_jump_latest.pack(side=tk.RIGHT, padx=2)

        self.btn_jump_val = ttk.Button(self.dissect_header_frame, text="Jump to Latest 'val:'", command=self.jump_to_latest_val_msg)
        self.btn_jump_val.pack(side=tk.RIGHT, padx=2)

        self.dissector_tree = ttk.Treeview(self.dissector_frame, columns=("Value"), show="tree headings")
        self.dissector_tree.heading("#0", text="Key / Index")
        self.dissector_tree.heading("Value", text="Value")
        
        self.dissector_tree.column("#0", width=200, anchor="w")
        self.dissector_tree.column("Value", width=400, anchor="w")
        
        self.dissector_scroll_y = ttk.Scrollbar(self.dissector_frame, orient=tk.VERTICAL, command=self.dissector_tree.yview)
        self.dissector_tree.configure(yscrollcommand=self.dissector_scroll_y.set)
        
        self.dissector_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.dissector_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Controls
        self.btn_clear = ttk.Button(self.main_frame, text="Clear Log", command=self.clear_log)
        self.btn_clear.pack(side=tk.BOTTOM, pady=5)

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
                if "val" in data:
                    val_display = str(data["val"])
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

    def jump_to_latest_val_msg(self):
        """Finds the most recent log entry containing a 'val' key and selects it."""
        for item_id in self.log_tree.get_children():
            values = self.log_tree.item(item_id, "values")
            if values and len(values) >= 7:
                payload = values[6]
                try:
                    data = orjson.loads(payload)
                    if isinstance(data, dict) and "val" in data:
                        # Select and focus
                        self.log_tree.selection_set(item_id)
                        self.log_tree.see(item_id)
                        self.log_tree.focus(item_id)
                        # Trigger dissector update
                        self.on_log_select()
                        return
                except Exception as e:
                    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Skipping log entry in jump_to_latest_val_msg: {e}", "TRACE")
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