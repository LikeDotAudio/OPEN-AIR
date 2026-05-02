# oaComProtocols.oaComNmos/Interface/nmos_commands_monitor_impl.py
# Author: Gemini (Collaborator)
# Version: 20260405.2145.3
#
# Description: NMOS Commands Monitor Implementation.
# Displays a log of NMOS IS-07 events and resource updates.

import json
import time
import tkinter as tk
from tkinter import ttk

from oaLogging.Methods.matrix_gate import matrix_log

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGui.Workers.compositing.sync_behavior import SyncBehavior
except ImportError:
    class SyncBehavior:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass

class NmosCommandsMonitorImplementation(tk.Frame, SyncBehavior):
    """
    NMOS Commands Monitor GUI.
    Provides a real-time view of IS-07 events and resource updates.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}

        self._setup_ui()

        from oaComProtocols.oaComNmos.Core.event_bus import nmos_event_bus
        nmos_event_bus.subscribe("NMOS_EVENT", self._on_nmos_event)

        # ⚡ PRIME FROM CACHE: If state_cache is provided, populate the view
        if self.config.get("state_cache"):
            self.prime_from_cache(self.config["state_cache"])

    def prime_from_cache(self, state_cache):
        """Populates the tree with current values from the global state cache."""
        try:
            # Get a snapshot of the current state
            cache_snapshot = state_cache.rust_cache.to_dict()
            for topic, payload in cache_snapshot.items():
                if "NMOS" in topic.upper(): continue
                # Normalize payload
                data = payload.get("value") if isinstance(payload, dict) else payload
                self._add_event("CACHE", "INITIAL_STATE", topic, data)
        except Exception as e:
            matrix_log("comms", "nmos", "prime_from_cache", f"Failed to prime NMOS monitor: {e}", "WARNING")

    def _on_nmos_event(self, transport, etype, eid, payload):
        self.after(0, lambda: self._add_event(transport, etype, eid, payload))

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        bg_color = self.cget("bg") or "#2b2b2b"
        self.configure(bg=bg_color)

        # 1. Header
        header = tk.Frame(self, bg=bg_color)
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="📝 NMOS COMMANDS & EVENTS", font=("Helvetica", 14, "bold"), fg="#ffffff", bg=bg_color).pack(side=tk.LEFT, padx=20)

        # 2. Table Panel
        table_frame = tk.Frame(self, bg=bg_color)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        cols = ("Time", "Transport", "Type", "ID", "Payload")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.column("Payload", width=300)
        self.tree.column("ID", width=150)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 3. Footer / Details
        detail_frame = tk.LabelFrame(self, text=" Event Details ", bg=bg_color, fg="#888888", padx=10, pady=10)
        detail_frame.pack(fill=tk.X, padx=20, pady=10)

        self.detail_text = tk.Text(detail_frame, height=4, bg="#000000", fg="#00ff00", font=("Courier", 10))
        self.detail_text.pack(fill=tk.X)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # 4. Controls
        ctrl_frame = tk.Frame(self, bg=bg_color)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)
        ttk.Button(ctrl_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT)

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        payload = item['values'][4]
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, payload)

    def _clear_log(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.detail_text.delete("1.0", tk.END)

    def _add_event(self, transport, etype, eid, payload):
        timestamp = time.strftime("%H:%M:%S")
        self.tree.insert("", 0, values=(timestamp, transport, etype, eid, json.dumps(payload)))
        if len(self.tree.get_children()) > 100:
            self.tree.delete(self.tree.get_children()[-1])

    def render(self):
        self.configure(bg=self.cget("bg"))

    def destroy(self):
        self.running = False
        super().destroy()

__all__ = ["NmosCommandsMonitorImplementation"]
