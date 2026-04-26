# oaGuiElements/Core/utils/knob_rotary_selector/Interface/knob_rotary_selector_editor.py
# Author: Gemini CLI
# Version: 20260417.1.0
# Description: Bespoke editor for knob_rotary_selector.

import tkinter as tk


class KnobRotarySelectorEditor:
    """Standalone editor for knob_rotary_selector configuration."""

    def __init__(self, parent, config_data, on_save_callback):
        self.parent = parent
        self.current_config = config_data.copy() if config_data else {}
        self.on_save = on_save_callback

        self.window = tk.Toplevel(parent)
        self.window.title(f"Editor: {self.current_config.get('path', 'knob_rotary_selector')}")
        self.window.geometry("500x600")
        self.window.configure(bg="#1e1e1e")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        header = tk.Frame(self.window, bg="#333333", height=40)
        header.pack(side="top", fill="x")
        tk.Label(header, text="KNOB ROTARY SELECTOR EDITOR", bg="#333333", fg="white",
                 font=("Arial", 10, "bold")).pack(side="left", padx=10, pady=10)

        container = tk.Frame(self.window, bg="#1e1e1e")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(container, text="Bespoke properties for knob_rotary_selector will appear here.", bg="#1e1e1e", fg="white").pack(pady=20)

        row = tk.Frame(container, bg="#1e1e1e")
        row.pack(fill="x", pady=5)
        tk.Label(row, text="Label", bg="#1e1e1e", fg="#dcdcdc", width=15, anchor="w").pack(side="left")
        var = tk.StringVar(value=str(self.current_config.get("label", "")))
        entry = tk.Entry(row, textvariable=var, bg="#2d2d2d", fg="white", insertbackground="white", relief="flat")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        var.trace_add("write", lambda *a: self.current_config.update({"label": var.get()}))

        footer = tk.Frame(self.window, bg="#333333", height=50)
        footer.pack(side="bottom", fill="x")

        tk.Button(footer, text="SAVE", bg="#4CAF50", fg="white",
                  font=("Arial", 9, "bold"), relief="flat", width=12,
                  command=self._on_save).pack(side="right", padx=10, pady=10)

        tk.Button(footer, text="DISCARD", bg="#f44336", fg="white",
                  font=("Arial", 9, "bold"), relief="flat", width=12,
                  command=self.window.destroy).pack(side="right", padx=10, pady=10)

    def _on_save(self):
        if self.on_save:
            self.on_save(self.current_config)
        self.window.destroy()

    @staticmethod
    def launch(parent, config_data, on_save_callback):
        return KnobRotarySelectorEditor(parent, config_data, on_save_callback)
