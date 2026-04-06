# oaComNmos/Interface/nmos_commands_monitor_impl.py
# Author: Gemini (Collaborator)
# Version: 20260405.2145.3
#
# Description: NMOS Commands Monitor Implementation.
# Displays a log of NMOS IS-07 events and resource updates.

import tkinter as tk
from tkinter import ttk
import threading
import time
import json
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaLogging.Methods.matrix_gate import matrix_log

class NmosCommandsMonitorImplementation(tk.Frame, TransparencyMixin):
    """
    NMOS Commands Monitor GUI.
    Provides a real-time view of IS-07 events and resource updates.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}
        
        self._setup_ui()
        self._start_simulation()

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

    def _start_simulation(self):
        self.running = True
        self.sim_thread = threading.Thread(target=self._sim_loop, daemon=True)
        self.sim_thread.start()

    def _sim_loop(self):
        # Simulate some NMOS events
        events = [
            ("MQTT", "State Change", "source-1", {"val": True}),
            ("WS", "Update", "flow-2", {"status": "active"}),
            ("MQTT", "Heartbeat", "node-0", {"health": "ok"}),
        ]
        i = 0
        while self.running:
            if i < len(events):
                evt = events[i]
                self.after(0, lambda e=evt: self._add_event(*e))
                i += 1
            time.sleep(10) # Low frequency simulation

    def _add_event(self, transport, etype, eid, payload):
        ts = time.strftime("%H:%M:%S")
        self.tree.insert("", 0, values=(ts, transport, etype, eid, json.dumps(payload)))
        if len(self.tree.get_children()) > 100:
            self.tree.delete(self.tree.get_children()[-1])

    def render(self):
        self.configure(bg=self.cget("bg"))

    def destroy(self):
        self.running = False
        super().destroy()

__all__ = ["NmosCommandsMonitorImplementation"]
