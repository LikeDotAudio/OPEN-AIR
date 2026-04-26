# oaComProtocols.oaComSNMP/Interface/snmp_log_impl.py
# Author: Anthony Peter Kuzub
# Version: 20260405.2130.1
#
# Description: SNMP Delta Monitor Implementation (Reverted to legacy functionality).

import tkinter as tk
from tkinter import ttk

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGui.Core.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass

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

        # ⚡ STANDALONE: Prioritize injected manager
        self.app_instance = self.config.get("app_instance")
        if self.app_instance:
            self.snmp_manager = getattr(self.app_instance, 'snmp_manager', None)
        else:
            self.snmp_manager = self._find_snmp_manager(parent)

        # Fallback: Find manager via Entry if still not found
        if not self.snmp_manager:
            try:
                from oaComProtocols.oaComSNMP.Entry import get_manager
                self.snmp_manager = get_manager()
            except Exception: pass

        # State tracking: { OID: last_value }
        self._last_values = {}
        # Entry IDs: { OID: TreeviewID }
        self._oid_to_item = {}
        # Metadata cache: { OID: metadata_dict }
        self._oid_metadata = {}
        # Tag cache: { OID: last_tag_set } to avoid redundant Treeview updates
        self._item_tags = {}

        # Update buffering for high-velocity traffic
        self._update_buffer = []
        self._update_scheduled = False

        self._setup_ui()

        if self.snmp_manager:
            # ? INITIAL POPULATION: Don't wait for the next periodic dump
            # Use the manager's current OID map to fill the list immediately
            # We buffer these to ensure the UI remains responsive during startup
            initial_map = getattr(self.snmp_manager.oid_map_converter, "oid_map", {})
            for oid, data in initial_map.items():
                self._update_buffer.append((oid, data.get('value'), data.get('topic'), data))

            if self._update_buffer:
                self._update_scheduled = True
                self.after(10, self._process_update_buffer)

            self.snmp_manager.add_monitor_callback(self.on_snmp_traffic)

    def _find_snmp_manager(self, widget):
        """
        ⚡ DECOUPLED: Searches the widget tree for an SNMP manager without 
        direct dependency on oaGui classes.
        """
        curr = widget
        while curr:
            # 1. Direct Attribute Check
            if hasattr(curr, 'snmp_manager'):
                return curr.snmp_manager

            # 2. App Instance Check (Generic pattern)
            app = getattr(curr, 'app_instance', None)
            if app and hasattr(app, 'snmp_manager'):
                return app.snmp_manager

            try: curr = curr.master
            except: break
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
        if direction not in ["TX_DUMP", "RX", "RX_SET"]: return

        # ? BATCHING: Buffer updates to avoid flooding the event loop
        self._update_buffer.append((oid, value, topic, metadata))

        if not self._update_scheduled:
            self._update_scheduled = True
            # Process buffer every 100ms for responsiveness without lag
            self.after(100, self._process_update_buffer)

    def _process_update_buffer(self):
        if not self._update_buffer:
            self._update_scheduled = False
            return

        # ? CHUNKING: Process at most 100 items at a time to keep UI responsive
        chunk_size = 100
        chunk = self._update_buffer[:chunk_size]
        self._update_buffer = self._update_buffer[chunk_size:]

        for oid, value, topic, metadata in chunk:
            self._update_oid_state(oid, value, topic, metadata)

        # Update Counter once per batch
        self.counter_var.set(f"Total Objects: {len(self._last_values)}")

        # If more items remain, schedule another pass quickly
        if self._update_buffer:
            self.after(20, self._process_update_buffer)
        else:
            self._update_scheduled = False

    def _update_oid_state(self, oid, value, topic, metadata):
        prev_val = self._last_values.get(oid, None)

        has_changed = (prev_val is not None and str(prev_val) != str(value))
        is_new = (prev_val is None)

        if not is_new and not has_changed:
            # ? OPTIMIZATION: Only update tag if it's not already 'stale'
            if oid in self._oid_to_item:
                if self._item_tags.get(oid) != "stale":
                    item_id = self._oid_to_item[oid]
                    self.tree.item(item_id, tags=("stale",))
                    self._item_tags[oid] = "stale"
            return

        # Update State
        self._last_values[oid] = value
        if metadata:
            self._oid_metadata[oid] = metadata

        # Update UI
        if oid in self._oid_to_item:
            item_id = self._oid_to_item[oid]

            # Update values if changed
            if has_changed:
                self.tree.item(item_id, values=(oid, value, prev_val or "-", topic or "-"))
                # ? MOVE TO TOP and highlight green on change
                # Only move if not already at the top to save CPU
                if self.tree.index(item_id) != 0:
                    self.tree.move(item_id, "", 0)

                self.tree.item(item_id, tags=("changed",))
                self._item_tags[oid] = "changed"
        else:
            # ? NEW DISCOVERY: First Cycle Highlight (Yellow BG, Red Text)
            item_id = self.tree.insert("", 0, values=(oid, value, "-", topic or "-"), tags=("new_discovery",))
            self._oid_to_item[oid] = item_id
            self._item_tags[oid] = "new_discovery"

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

        # ⚡ SYNC: Request a fresh state dump from the manager
        if self.snmp_manager and hasattr(self.snmp_manager, "reset_monitor_state"):
            self.snmp_manager.reset_monitor_state()

    def render(self):
        self.configure(bg=self.cget("bg"))

    def destroy(self):
        if self.snmp_manager:
            self.snmp_manager.remove_monitor_callback(self.on_snmp_traffic)
        super().destroy()

__all__ = ["SnmpLogImplementation"]
