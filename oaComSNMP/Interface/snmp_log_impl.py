# oaComSNMP/Interface/snmp_log_impl.py
# Author: Anthony Peter Kuzub
# Version: 20260405.2130.1
#
# Description: SNMP Delta Monitor Implementation (Reverted to legacy functionality).

import tkinter as tk
from tkinter import ttk
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
import os
import sys
import pathlib
from pathlib import Path
import inspect
from oaLogging.Methods.matrix_gate import matrix_log
from loguru import logger
import orjson

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False

class SnmpLogImplementation(tk.Frame, TransparencyMixin):
    """
    Advanced SNMP Monitor with Change Tracking and Smart Sorting.
    - Green (Top): Value changed in this refresh.
    - Yellow (Bottom): No change.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}
        
        # ? DEPENDENCY INJECTION: Use the app_instance from the config if available
        self.app_instance = self.config.get("app_instance")
        if self.app_instance:
            self.snmp_manager = getattr(self.app_instance, 'snmp_manager', None)
        else:
            self.snmp_manager = self._find_snmp_manager(parent)
        
        # State tracking: { OID: last_value }
        self._last_values = {}
        # Entry IDs: { OID: TreeviewID }
        self._oid_to_item = {}
        # Metadata cache: { OID: metadata_dict }
        self._oid_metadata = {}
        
        self._setup_ui()
        
        if self.snmp_manager:
            self.snmp_manager.add_monitor_callback(self.on_snmp_traffic)

    def _find_snmp_manager(self, widget):
        from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
        from oaLogging.Methods.matrix_gate import matrix_log
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder):
                manager = getattr(curr.app_instance, 'snmp_manager', None)
                if LOCAL_DEBUG:
                    matrix_log("ui", "snmp", "_find_snmp_manager", f"📡 [DEBUG] SnmpLog: Found DynamicGuiBuilder. App instance has snmp_manager: {manager is not None}")
                return manager
            try: curr = curr.master
            except: break
        if LOCAL_DEBUG:
            matrix_log("ui", "snmp", "_find_snmp_manager", "?? [DEBUG] SnmpLog: Failed to find snmp_manager in ancestor chain.", "WARNING")
        return None

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        
        # 1. Header Frame
        header_frame = tk.Frame(self, bg=self.cget("bg"))
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        lbl = ttk.Label(header_frame, text="SNMP Delta Monitor", font=("Helvetica", 12, "bold"), background=self.cget("bg"))
        lbl.pack(side=tk.LEFT, padx=10)

        self.counter_var = tk.StringVar(value="Total Objects: 0")
        ttk.Label(header_frame, textvariable=self.counter_var, font=("Courier", 10, "bold"), foreground="#00ff00", background=self.cget("bg")).pack(side=tk.RIGHT, padx=20)

        # 2. Split View (Monitor + Investigation)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Delta Monitor ---
        monitor_frame = tk.Frame(self.paned, bg=self.cget("bg"))
        self.paned.add(monitor_frame, weight=3)

        # Enhanced Columns for Delta Tracking
        cols = ("OID", "Current Value", "Previous Value", "Topic")
        self.tree = ttk.Treeview(monitor_frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        self.tree.column("OID", width=250)
        self.tree.column("Topic", width=300)
        
        # Tags for change state
        self.tree.tag_configure("changed", foreground="#00ff00") # Bright Green
        self.tree.tag_configure("stale", foreground="#888800")   # Dim Yellow
        self.tree.tag_configure("new_discovery", background="yellow", foreground="red") # First Cycle Highlight
        
        scroll = ttk.Scrollbar(monitor_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_oid)

        # --- BOTTOM: Investigation Pane ---
        inspect_frame = tk.Frame(self.paned, bg="#000000", bd=1, relief="sunken")
        self.paned.add(inspect_frame, weight=2)

        tk.Label(inspect_frame, text="?? SNMP MESSAGE DISSECTOR", font=("Helvetica", 10, "bold"), fg="#888888", bg="#000000").pack(anchor="nw", padx=5)
        
        self.inspect_text = tk.Text(inspect_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), bd=0, highlightthickness=0)
        self.inspect_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.inspect_text.tag_configure("header", foreground="#ffffff", font=("Courier", 10, "bold"))

        # 3. Footer (Buttons)
        btn_frame = tk.Frame(self, bg=self.cget("bg"))
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Clear Tracker", command=self.clear_log).pack(side=tk.LEFT, padx=10)

    def on_snmp_traffic(self, direction, oid, value, topic, metadata=None):
        # Handle both periodic dumps and real-time changes
        if LOCAL_DEBUG:
            from oaLogging.Methods.matrix_gate import matrix_log
            # ? SAFETY: Use repr() to ensure non-printable chars (like \r, \n, \b) are escaped
            matrix_log("ui", "snmp", "on_snmp_traffic", f"?? [TRAFFIC] Dir: {direction}, OID: {oid}, Val: {repr(value)[:100]}")
        
        if direction not in ["TX_DUMP", "RX", "RX_SET"]: return
        
        self.after(0, lambda: self._update_oid_state(oid, value, topic, metadata))

    def _update_oid_state(self, oid, value, topic, metadata):
        prev_val = self._last_values.get(oid, None)
        
        # ? OPTIMIZATION: If value hasn't changed, don't update 'Previous Value' 
        # unless it's a new discovery. This keeps the delta meaningful.
        has_changed = (prev_val is not None and str(prev_val) != str(value))
        is_new = (prev_val is None)
        
        if not is_new and not has_changed:
            # If nothing changed, we just refresh the "stale" tag to show it's still alive
            if oid in self._oid_to_item:
                item_id = self._oid_to_item[oid]
                self.tree.item(item_id, tags=("stale",))
            return

        # Update State
        if has_changed:
            # We only store the "old" value when a REAL change occurs.
            # This prevents periodic TX_DUMP from overwriting the meaningful history.
            self._last_values[oid] = value
        elif is_new:
            self._last_values[oid] = value

        if metadata:
            self._oid_metadata[oid] = metadata
        
        # Update UI
        if oid in self._oid_to_item:
            item_id = self._oid_to_item[oid]
            
            # If changed, we show the transition. If it's a redundant TX_DUMP,
            # this part is skipped by the 'not has_changed' check above.
            self.tree.item(item_id, values=(oid, value, prev_val or "-", topic or "-"))
            
            if has_changed:
                # ? MOVE TO TOP and highlight green on change
                self.tree.move(item_id, "", 0)
                self.tree.item(item_id, tags=("changed",))
        else:
            # ? NEW DISCOVERY: First Cycle Highlight (Yellow BG, Red Text)
            item_id = self.tree.insert("", 0, values=(oid, value, "-", topic or "-"), tags=("new_discovery",))
            self._oid_to_item[oid] = item_id

        # Update Counter
        self.counter_var.set(f"Total Objects: {len(self._last_values)}")

    def on_select_oid(self, event):
        """Populates the investigation pane with detailed metadata for the selected OID."""
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        oid = item["values"][0]
        metadata = self._oid_metadata.get(oid)
        
        self.inspect_text.delete("1.0", tk.END)
        self.inspect_text.insert(tk.END, "????????????? SNMP MESSAGE DISSECTION ?????????????\n", "header")
        self.inspect_text.insert(tk.END, f"  OID        : {oid}\n")
        self.inspect_text.insert(tk.END, f"  VALUE      : {item['values'][1]}\n")
        self.inspect_text.insert(tk.END, f"  TOPIC      : {item['values'][3]}\n")
        
        if metadata:
            self.inspect_text.insert(tk.END, "????????????????????????????????????????????????????\n")
            desc = metadata.get("descriptor", "Unknown")
            path = " -> ".join(metadata.get("path_parts", []))
            
            self.inspect_text.insert(tk.END, f"  DESCRIPTOR : {desc}\n")
            self.inspect_text.insert(tk.END, f"  PATH       : {path}\n")
            
            self.inspect_text.insert(tk.END, "??? RAW METADATA ???????????????????????????????????\n")
            import orjson
            pretty_json = orjson.dumps(metadata, option=orjson.OPT_INDENT_2).decode()
            self.inspect_text.insert(tk.END, f"{pretty_json}\n")
            
        self.inspect_text.insert(tk.END, "?????????????????????? END ?????????????????????????\n")

    def clear_log(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._last_values.clear()
        self._oid_to_item.clear()
        self._oid_metadata.clear()
        self.counter_var.set("Total Objects: 0")

    def render(self):
        self.configure(bg=self.cget("bg"))

    def destroy(self):
        if self.snmp_manager:
            self.snmp_manager.remove_monitor_callback(self.on_snmp_traffic)
        super().destroy()

__all__ = ["SnmpLogImplementation"]
