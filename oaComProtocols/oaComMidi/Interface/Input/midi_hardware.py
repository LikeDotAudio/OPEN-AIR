# oaComProtocols.oaComMidi/Interface/midi_hardware.py
#
# MIDI Hardware Port List Component.
#
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1

import tkinter as tk
from tkinter import ttk


class MidiHardware(tk.Frame):
    """
    Detected Hardware Ports list component.
    """
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        super().__init__(parent, **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")
        self.port_tree = ttk.Treeview(self, columns=("Type", "Status"), show="tree headings", height=8)
        self.port_tree.column("#0", width=150, stretch=tk.YES) # Device Name
        self.port_tree.column("Type", width=80, stretch=tk.NO)  # Type
        self.port_tree.column("Status", width=100, stretch=tk.NO) # Status
        self.port_tree.heading("#0", text="Device Name")
        self.port_tree.heading("Type", text="Type")
        self.port_tree.heading("Status", text="Status")
        self.port_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.port_tree.tag_configure("input", foreground="#00aaff")
        self.port_tree.tag_configure("output", foreground="#ffaa00")

    def update_ports(self, info):
        # Clear existing
        for item in self.port_tree.get_children():
            self.port_tree.delete(item)

        if not info or info.get("error"):
            error = info.get("error") if info else "No info"
            self.port_tree.insert("", "end", text="ERROR", values=("FAIL", error))
            return

        # Populate Inputs
        for name in info.get("inputs", []):
            status = "Active" if name in info.get("active_in", []) else "Available"
            self.port_tree.insert("", "end", text=name, values=("INPUT", status), tags=("input",))

        # Populate Outputs
        for name in info.get("outputs", []):
            status = "Active" if name in info.get("active_out", []) else "Available"
            self.port_tree.insert("", "end", text=name, values=("OUTPUT", status), tags=("output",))
