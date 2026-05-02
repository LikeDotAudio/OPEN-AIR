# 3_Command_Router/command_router_legend.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Encapsulates the symbol and color key sidebar for the Command Router.

import tkinter as tk

class CommandRouterLegend(tk.Frame):
    """Encapsulates the symbol and color key sidebar."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1a1a1a", bd=1, relief="raised", width=200, **kwargs)
        self.pack_propagate(False)
        self._setup_sections()

    def _setup_sections(self):
        tk.Label(self, text="🗝️ SYMBOL KEY", font=("Helvetica", 9, "bold"), fg="#ffffff", bg="#333333").pack(fill=tk.X)
        symbols = [("🚀", "PUSH", "Network Out"), ("💾", "CACHE", "State Registry"), ("Ⓖ", "GUI", "Local Interface"), ("🅾️", "OSC", "OSC Protocol"), ("🎹", "MIDI", "MIDI Hardware"), ("Ⓜ️", "MQTT", "Broker Reflect"), ("Ⓢ", "SNMP", "Network Infra"), ("🔗", "LINK", "Splink Active")]
        for sym, name, desc in symbols:
            f = tk.Frame(self, bg="#1a1a1a"); f.pack(fill=tk.X, padx=5, pady=1)
            tk.Label(f, text=sym, font=("Helvetica", 10), fg="#00ff00", bg="#1a1a1a", width=2).pack(side=tk.LEFT)
            tk.Label(f, text=f"{name: <6}", font=("Courier", 8, "bold"), fg="#888888", bg="#1a1a1a").pack(side=tk.LEFT)
            tk.Label(f, text=desc, font=("Helvetica", 7), fg="#666666", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        tk.Label(self, text="🎨 COLOR KEY", font=("Helvetica", 9, "bold"), fg="#ffffff", bg="#333333").pack(fill=tk.X, pady=(10, 0))
        colors = [("HERE", "#00ff00", None, "This Machine"), ("REMOTE", "yellow", "#440000", "Other Machine"), ("MUTATION", "red", "#440000", "Hardware Ctrl"), ("MIDI", "#ff00ff", None, "MIDI Traffic"), ("OSC", "#00ffff", None, "OSC Traffic"), ("SYSTEM", "#888888", None, "Internal/Init"), ("SPLINK", "#a0a0a0", "#1a1a1a", "Brokered Link")]
        for name, fg, bg, desc in colors:
            f = tk.Frame(self, bg="#1a1a1a"); f.pack(fill=tk.X, padx=5, pady=1)
            tk.Label(f, text=name, font=("Courier", 8, "bold"), fg=fg, bg=bg or "#1a1a1a", width=8).pack(side=tk.LEFT)
            tk.Label(f, text=desc, font=("Helvetica", 7), fg="#666666", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)
