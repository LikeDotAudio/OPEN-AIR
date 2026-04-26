# oaComProtocols.oaComMidi/Interface/midi_hardware_search.py
#
# MIDI Hardware Search & Refresh Component.
#
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1

import tkinter as tk
from tkinter import ttk


class MidiHardwareSearch(tk.Frame):
    """
    Component for hardware refresh and search actions.
    """
    def __init__(self, parent, refresh_callback=None, **kwargs):
        self.config_data = kwargs.pop("config", {})
        self.refresh_callback = refresh_callback
        super().__init__(parent, **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")
        ttk.Button(self, text="🔄 Refresh MIDI Hardware", command=self.refresh_callback).pack(side=tk.LEFT, padx=5, pady=5)

        # Search Entry placeholder for future filtering
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self, textvariable=self.search_var)
        self.search_entry.pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Label(self, text="Filter:", bg="#2b2b2b", fg="#ffffff").pack(side=tk.RIGHT)
