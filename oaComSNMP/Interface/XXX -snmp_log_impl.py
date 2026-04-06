# /home/anthony/Documents/OPEN-AIR/oaComSNMP/Interface/snmp_log_impl.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: SNMP Delta Monitor Implementation.

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
import orjson # Imported for potential use in metadata display if needed, though not directly in this class's current logic.

# --- Path Guard: Ensure project root is in sys.path if needed by sub-modules ---
# This might need adjustment based on how oaComSNMP is structured and accessed.
# For now, assuming direct imports work or external path setup is handled elsewhere.

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True

class SnmpLogImplementation(tk.Frame, TransparencyMixin):
    """
    Advanced SNMP Monitor with Change Tracking and Smart Sorting.
    - Green (Top): Value changed in this refresh.
    - Yellow (Bottom): No change.
    This class contains the full implementation logic.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}
        
        # ? DEPENDENCY INJECTION: Use the app_instance from the config if available
        self.app_instance = self.config.get("app_instance")
        if self.app_instance:
            self.snmp_manager = getattr(self.app_instance, 'snmp_manager', None)
        else:
            # Fallback to searching the widget hierarchy if app_instance is not provided
            self.snmp_manager = self._find_snmp_manager(parent)
        
        # State tracking: { OID: last_value }
        self._last_values = {}
        # Entry IDs: { OID: TreeviewID }
        self._oid_to_item = {}
        # Metadata cache: { OID: metadata_dict }
        self._oid_metadata = {}
        
        self._setup_ui()
        
        if self.snmp_manager:
            # Register the callback to receive SNMP traffic updates
            self.snmp_manager.add_monitor_callback(self.on_snmp_traffic)
        else:
            if LOCAL_DEBUG:
                matrix_log("ui", "snmp", "__init__", "?? [DEBUG] SnmpLogImplementation: SNMP Manager not found. Monitoring will be disabled.", "WARNING")

    def _find_snmp_manager(self, widget):
        """
        Recursively searches the widget hierarchy to find the SNMP manager.
        This is a fallback mechanism if dependency injection is not used.
        """
        try:
            from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
            curr = widget
            while curr:
                if isinstance(curr, DynamicGuiBuilder) and hasattr(curr, 'app_instance'):
                    manager = getattr(curr.app_instance, 'snmp_manager', None)
                    if LOCAL_DEBUG:
                        matrix_log("ui", "snmp", "_find_snmp_manager", f"?? [DEBUG] Found DynamicGuiBuilder. App instance has snmp_manager: {manager is not None}")
                    return manager
                try: curr = curr.master
                except: break # Stop if master attribute is not available (e.g., root widget)
            if LOCAL_DEBUG:
                matrix_log("ui", "snmp", "_find_snmp_manager", "?? [DEBUG] Failed to find snmp_manager in ancestor chain.", "WARNING")
        except ImportError:
            if LOCAL_DEBUG:
                matrix_log("ui", "snmp", "_find_snmp_manager", "?? [DEBUG] oaGuiBuilder not found, cannot search for snmp_manager.", "WARNING")
        except Exception as e:
            if LOCAL_DEBUG:
                matrix_log("ui", "snmp", "_find_snmp_manager", f"?? [DEBUG] An unexpected error occurred: {e}", "ERROR")
        return None

    def _setup_ui(self):
        """Initializes the graphical user interface components."""
        self.pack(fill=tk.BOTH, expand=True)
        
        # Use the background color from Tkinter's configuration, defaulting if not set
        bg_color = self.cget("bg") if self.cget("bg") else "#2b2b2b" 
        self.configure(bg=bg_color)

        # 1. Header Frame
        header_frame = tk.Frame(self, bg=bg_color)
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        lbl = ttk.Label(header_frame, text="SNMP Delta Monitor", font=("Helvetica", 12, "bold"), background=bg_color)
        lbl.pack(side=tk.LEFT, padx=10)

        self.counter_var = tk.StringVar(value="Total Objects: 0")
        ttk.Label(header_frame, textvariable=self.counter_var, font=("Courier", 10, "bold"), foreground="#00ff00", background=bg_color).pack(side=tk.RIGHT, padx=20)

        # 2. Split View (Monitor + Investigation)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL, sashwidth=4, bg=bg_color)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Delta Monitor ---
        monitor_frame = tk.Frame(self.paned, bg=bg_color)
        self.paned.add(monitor_frame, stretch="always", height=300) # Give it a default height

        # Enhanced Columns for Delta Tracking
        cols = ("OID", "Current Value", "Previous Value", "Topic")
        self.tree = ttk.Treeview(monitor_frame, columns=cols, show="headings", style="Treeview") # Use default style for now
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        self.tree.column("OID", width=250)
        self.tree.column("Topic", width=300)
        
        # Tags for change state
        self.tree.tag_configure("changed", foreground="#00ff00") # Bright Green for new/changed values
        self.tree.tag_configure("stale", foreground="#888800")   # Dim Yellow for values that haven't changed
        self.tree.tag_configure("new_discovery", background="yellow", foreground="red") # First Cycle Highlight for new OIDs
        
        scroll = ttk.Scrollbar(monitor_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_oid)

        # --- BOTTOM: Investigation Pane ---
        inspect_frame = tk.Frame(self.paned, bg="#000000", bd=1, relief="sunken")
        self.paned.add(inspect_frame, stretch="always", height=200) # Give it a default height

        tk.Label(inspect_frame, text="?? SNMP MESSAGE DISSECTOR", font=("Helvetica", 10, "bold"), fg="#888888", bg="#000000").pack(anchor="nw", padx=5, pady=2)
        
        # Text widget for displaying detailed information
        self.inspect_text = tk.Text(inspect_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), bd=0, highlightthickness=0, wrap=tk.WORD)
        self.inspect_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.inspect_text.tag_configure("header", foreground="#ffffff", font=("Courier", 10, "bold"))

        # 3. Footer (Buttons)
        btn_frame = tk.Frame(self, bg=bg_color)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Clear Tracker", command=self.clear_log).pack(side=tk.LEFT, padx=10)

    def on_snmp_traffic(self, direction, oid, value, topic, metadata=None):
        """
        Callback function to process incoming SNMP traffic data.
        Handles both periodic dumps and real-time changes.
        """
        if LOCAL_DEBUG:
            # Use repr() to ensure non-printable characters are properly displayed in logs
            matrix_log("ui", "snmp", "on_snmp_traffic", f"?? [TRAFFIC] Dir: {direction}, OID: {oid}, Val: {repr(value)[:100]}")
        
        # Filter out irrelevant directions
        if direction not in ["TX_DUMP", "RX", "RX_SET"]: 
            return
        
        # Schedule UI update to run in the main Tkinter thread
        self.after(0, lambda: self._update_oid_state(oid, value, topic, metadata))

    def _update_oid_state(self, oid, value, topic, metadata):
        """
        Updates the internal state and the UI treeview based on new SNMP data.
        Tracks changes and highlights them.
        """
        prev_val = self._last_values.get(oid, None)
        
        # Determine if the value has changed or if it's a new OID discovery
        has_changed = (prev_val is not None and str(prev_val) != str(value))
        is_new = (prev_val is None)
        
        # Optimization: If value hasn't changed and it's not a new discovery,
        # only update the 'stale' tag to indicate the object is still alive.
        if not is_new and not has_changed:
            if oid in self._oid_to_item:
                item_id = self._oid_to_item[oid]
                self.tree.item(item_id, tags=("stale",)) # Mark as stale if no change
            return

        # Update internal state: store the current value as the last known value
        self._last_values[oid] = value
        if metadata:
            self._oid_metadata[oid] = metadata
        
        # Update UI Treeview
        if oid in self._oid_to_item:
            item_id = self._oid_to_item[oid]
            # Update the item with new values and apply 'changed' tag
            self.tree.item(item_id, values=(oid, value, prev_val or "-", topic or "-"))
            
            if has_changed:
                # Move changed items to the top for visibility and apply 'changed' tag
                self.tree.move(item_id, "", 0)
                self.tree.item(item_id, tags=("changed",))
        else:
            # For newly discovered OIDs, insert at the top and apply 'new_discovery' tag
            item_id = self.tree.insert("", 0, values=(oid, value, "-", topic or "-"), tags=("new_discovery",))
            self._oid_to_item[oid] = item_id

        # Update the total object count display
        self.counter_var.set(f"Total Objects: {len(self._last_values)}")

    def on_select_oid(self, event):
        """
        Handles selection of an item in the treeview.
        Populates the investigation pane with detailed metadata for the selected OID.
        """
        selected = self.tree.selection()
        if not selected: return
        
        item_id = selected[0]
        item = self.tree.item(item_id)
        oid = item["values"][0]
        metadata = self._oid_metadata.get(oid)
        
        # Clear previous content in the inspection text area
        self.inspect_text.delete("1.0", tk.END)
        self.inspect_text.insert(tk.END, "????????????? SNMP MESSAGE DISSECTION ?????????????
", "header")
        self.inspect_text.insert(tk.END, f"  OID        : {oid}
")
        self.inspect_text.insert(tk.END, f"  VALUE      : {item['values'][1]}
")
        self.inspect_text.insert(tk.END, f"  TOPIC      : {item['values'][3]}
")
        
        if metadata:
            self.inspect_text.insert(tk.END, "????????????????????????????????????????????????????
")
            desc = metadata.get("descriptor", "Unknown")
            path_parts = metadata.get("path_parts", [])
            path = " -> ".join(path_parts) if path_parts else "N/A"
            
            self.inspect_text.insert(tk.END, f"  DESCRIPTOR : {desc}
")
            self.inspect_text.insert(tk.END, f"  PATH       : {path}
")
            
            self.inspect_text.insert(tk.END, "??? RAW METADATA ???????????????????????????????????
")
            # Pretty print the raw metadata JSON
            try:
                pretty_json = orjson.dumps(metadata, option=orjson.OPT_INDENT_2).decode()
                self.inspect_text.insert(tk.END, f"{pretty_json}
")
            except Exception as e:
                self.inspect_text.insert(tk.END, f"Error formatting metadata: {e}
")
            
        self.inspect_text.insert(tk.END, "?????????????????????? END ?????????????????????????
")

    def clear_log(self):
        """Clears all tracked OIDs, their values, and metadata."""
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        self._last_values.clear()
        self._oid_to_item.clear()
        self._oid_metadata.clear()
        self.counter_var.set("Total Objects: 0")
        self.inspect_text.delete("1.0", tk.END) # Also clear the inspector

    def render(self):
        """Required by TransparencyMixin to sync background colors."""
        # Ensure background color is consistent if theme changes dynamically
        bg_color = self.cget("bg") if self.cget("bg") else "#2b2b2b"
        self.configure(bg=bg_color)
        # Also reconfigure child widgets if necessary, but for now, assume they inherit correctly.

    def destroy(self):
        """Cleanup resources when the widget is destroyed."""
        if self.snmp_manager:
            try:
                self.snmp_manager.remove_monitor_callback(self.on_snmp_traffic)
            except Exception as e:
                matrix_log("ui", "snmp", "destroy", f"Error removing monitor callback: {e}", "WARNING")
        super().destroy()

# Define __all__ for explicit export
__all__ = [
    "SnmpLogImplementation",
]
