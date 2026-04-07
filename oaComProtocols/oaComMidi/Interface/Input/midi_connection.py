# oaComProtocols.oaComMidi/Interface/midi_connection.py
#
# MIDI Port Connection & Status Component.
#
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1

import tkinter as tk
from tkinter import ttk

class MidiConnection(tk.Frame):
    """
    Component for managing and displaying a single MIDI connection.
    """
    def __init__(self, parent, port_name, port_type, status, **kwargs):
        self.config_data = kwargs.pop("config", {})
        self.port_name = port_name
        self.port_type = port_type # INPUT or OUTPUT
        super().__init__(parent, **kwargs)
        self._setup_ui(status)

    def _setup_ui(self, status):
        self.configure(bg="#333333", relief=tk.RAISED, bd=1)
        
        color = "#00aaff" if self.port_type == "INPUT" else "#ffaa00"
        tk.Label(self, text=f"[{self.port_type}]", fg=color, bg="#333333", font=("Helvetica", 8, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Label(self, text=self.port_name, fg="#ffffff", bg="#333333", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar(value=status)
        status_color = "#00ff00" if status == "Active" else "#888888"
        self.status_label = tk.Label(self, textvariable=self.status_var, fg=status_color, bg="#333333", font=("Helvetica", 8, "italic"))
        self.status_label.pack(side=tk.RIGHT, padx=5)

    def update_status(self, status):
        self.status_var.set(status)
        status_color = "#00ff00" if status == "Active" else "#888888"
        self.status_label.configure(fg=status_color)
