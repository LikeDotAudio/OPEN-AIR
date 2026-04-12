# oaComProtocols.oaComMidi/Interface/Input/midi_feed.py
#
# MIDI Live Feed Monitor Component.
#
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1

import tkinter as tk
import datetime
from .midi_keyboard import get_midi_color

class MidiFeed(tk.Frame):
    """
    Live MIDI Feed (Monitor) component.
    """
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        super().__init__(parent, **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")
        self.log_text = tk.Text(self, bg="#000000", fg="#00ff00", font=("Courier", 10), height=14, borderwidth=0, wrap='word')
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def add_log(self, direction, msg_str, channel=0):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        color = get_midi_color(channel)
        
        # Create or reuse a tag for this specific color
        tag_name = f"ch_color_{color.replace('#', '')}"
        self.log_text.tag_configure(tag_name, foreground=color)
        
        formatted_line = f"[{ts}] {direction} >> {msg_str}\n"
        self.log_text.insert("1.0", formatted_line, tag_name)
        
        # Truncate
        if int(self.log_text.index('end-1c').split('.')[0]) > 200:
            self.log_text.delete('200.0', tk.END)

    def clear(self):
        self.log_text.delete('1.0', tk.END)
