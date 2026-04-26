# oaComProtocols.oaComMidi/Interface/midi_connection_manager.py
#
# MIDI Port Connection Manager Component.
#
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1

import tkinter as tk

from .midi_connection import MidiConnection


class MidiConnectionManager(tk.Frame):
    """
    Component for managing multiple MIDI port connections.
    """
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        super().__init__(parent, **kwargs)
        self.connections = {}
        self._setup_ui()

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")
        self.container = tk.Frame(self, bg="#2b2b2b")
        self.container.pack(fill=tk.BOTH, expand=True)

    def update_connections(self, info):
        if not info or info.get("error"): return

        active_in = info.get("active_in", [])
        active_out = info.get("active_out", [])

        # This is a simplified view of active connections
        # In a real app, we'd sync this with the Treeview or provide a dedicated list
        for name in active_in:
            if name not in self.connections:
                conn = MidiConnection(self.container, name, "INPUT", "Active")
                conn.pack(fill=tk.X, padx=2, pady=1)
                self.connections[name] = conn

        for name in active_out:
            if name not in self.connections:
                conn = MidiConnection(self.container, name, "OUTPUT", "Active")
                conn.pack(fill=tk.X, padx=2, pady=1)
                self.connections[name] = conn
