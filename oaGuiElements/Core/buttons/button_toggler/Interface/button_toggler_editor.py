# oaGuiElements/Core/buttons/button_toggler/button_toggler_editor.py
# Author: Anthony Peter Kuzub / Gemini CLI
# Version: 20260417.1158.1
#
# Description: Bespoke editor for the Button Toggler element.
# Provides a standalone window to modify the element's JSON configuration.

import json
import tkinter as tk
from tkinter import colorchooser, ttk


class ButtonTogglerEditor:
    """Standalone editor for Button Toggler configuration."""

    def __init__(self, parent, config_data, on_save_callback):
        self.parent = parent
        self.original_config = config_data.copy()
        self.current_config = config_data.copy()
        self.on_save = on_save_callback

        self.window = tk.Toplevel(parent)
        self.window.title(f"Editor: {config_data.get('path', 'Button Toggler')}")
        self.window.geometry("600x800")
        self.window.configure(bg="#1e1e1e")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#333333", height=40)
        header.pack(side="top", fill="x")
        tk.Label(header, text="BUTTON TOGGLER EDITOR", bg="#333333", fg="white",
                 font=("Arial", 10, "bold")).pack(side="left", padx=10, pady=10)

        # Scrollable area
        container = tk.Frame(self.window, bg="#1e1e1e")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="#1e1e1e")

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self.canvas_window, width=e.width))

        # --- General Settings ---
        self._add_section("Layout & Behavior")
        self._add_entry("Label", "label")
        self._add_spinbox("Max Columns", "layout.max_cols", 1, 12)
        self._add_spinbox("Corner Radius", "layout.corner_radius", 0, 50)
        self._add_checkbox("Allow Null (Deselect All)", "Allow_Null")
        self._add_checkbox("Multi-Select Mode", "selection_mode", on_value="multi", off_value="one")

        # --- Colors ---
        self._add_section("Aesthetics")
        self._add_color_picker("Background Color", "bg_color")
        self._add_color_picker("Active Color", "active_color")
        self._add_color_picker("Active BG Color", "active_bg_color")
        self._add_color_picker("Text Color", "text_color")
        self._add_color_picker("Active Text Color", "active_text_color")
        self._add_slider("Glow Intensity", "glow_intensity", 0.0, 2.0)
        self._add_slider("Alpha (Transparency)", "alpha", 0.0, 1.0)

        # --- Options (Simplified for now) ---
        self._add_section("Options (Keys)")
        self.options_frame = tk.Frame(self.scroll_frame, bg="#1e1e1e")
        self.options_frame.pack(fill="x", pady=5)
        self._refresh_options_list()

        # Footer Actions
        footer = tk.Frame(self.window, bg="#333333", height=50)
        footer.pack(side="bottom", fill="x")

        tk.Button(footer, text="SAVE", bg="#4CAF50", fg="white",
                  font=("Arial", 9, "bold"), relief="flat", width=12,
                  command=self._on_save).pack(side="right", padx=10, pady=10)

        tk.Button(footer, text="DISCARD", bg="#f44336", fg="white",
                  font=("Arial", 9, "bold"), relief="flat", width=12,
                  command=self.window.destroy).pack(side="right", padx=10, pady=10)

    def _add_section(self, text):
        lbl = tk.Label(self.scroll_frame, text=text.upper(), bg="#1e1e1e", fg="#33A1FD",
                       font=("Arial", 9, "bold"))
        lbl.pack(fill="x", pady=(15, 5))
        tk.Frame(self.scroll_frame, height=1, bg="#444444").pack(fill="x", pady=(0, 10))

    def _get_nested(self, key_path):
        parts = key_path.split(".")
        val = self.current_config
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return None
        return val

    def _set_nested(self, key_path, value):
        parts = key_path.split(".")
        target = self.current_config
        for p in parts[:-1]:
            if p not in target or not isinstance(target[p], dict):
                target[p] = {}
            target = target[p]
        target[parts[-1]] = value

    def _add_entry(self, label, key_path):
        row = tk.Frame(self.scroll_frame, bg="#1e1e1e")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg="#1e1e1e", fg="#dcdcdc", width=20, anchor="w").pack(side="left")

        var = tk.StringVar(value=str(self._get_nested(key_path) or ""))
        entry = tk.Entry(row, textvariable=var, bg="#2d2d2d", fg="white", insertbackground="white", relief="flat")
        entry.pack(side="left", fill="x", expand=True, padx=5)

        var.trace_add("write", lambda *a: self._set_nested(key_path, var.get()))

    def _add_spinbox(self, label, key_path, from_, to_):
        row = tk.Frame(self.scroll_frame, bg="#1e1e1e")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg="#1e1e1e", fg="#dcdcdc", width=20, anchor="w").pack(side="left")

        val = self._get_nested(key_path)
        var = tk.IntVar(value=int(val) if val is not None else from_)
        spin = tk.Spinbox(row, from_=from_, to=to_, textvariable=var, bg="#2d2d2d", fg="white",
                          buttonbackground="#444444", relief="flat", width=5)
        spin.pack(side="left", padx=5)

        var.trace_add("write", lambda *a: self._set_nested(key_path, var.get()))

    def _add_checkbox(self, label, key_path, on_value=True, off_value=False):
        row = tk.Frame(self.scroll_frame, bg="#1e1e1e")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg="#1e1e1e", fg="#dcdcdc", width=20, anchor="w").pack(side="left")

        current = self._get_nested(key_path)
        var = tk.BooleanVar(value=(current == on_value))
        cb = tk.Checkbutton(row, variable=var, bg="#1e1e1e", activebackground="#1e1e1e",
                            selectcolor="#2d2d2d", highlightthickness=0)
        cb.pack(side="left", padx=5)

        var.trace_add("write", lambda *a: self._set_nested(key_path, on_value if var.get() else off_value))

    def _add_color_picker(self, label, key_path):
        row = tk.Frame(self.scroll_frame, bg="#1e1e1e")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg="#1e1e1e", fg="#dcdcdc", width=20, anchor="w").pack(side="left")

        color = self._get_nested(key_path) or "#000000"
        btn = tk.Button(row, bg=color, width=10, relief="flat")
        btn.pack(side="left", padx=5)

        def pick():
            c = colorchooser.askcolor(color, title=f"Pick {label}")[1]
            if c:
                btn.config(bg=c)
                self._set_nested(key_path, c)

        btn.config(command=pick)

    def _add_slider(self, label, key_path, from_, to_):
        row = tk.Frame(self.scroll_frame, bg="#1e1e1e")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg="#1e1e1e", fg="#dcdcdc", width=20, anchor="w").pack(side="left")

        val = self._get_nested(key_path)
        var = tk.DoubleVar(value=float(val) if val is not None else from_)
        scale = tk.Scale(row, from_=from_, to=to_, resolution=0.1, orient="horizontal",
                         variable=var, bg="#1e1e1e", fg="#888888", highlightthickness=0,
                         troughcolor="#2d2d2d", activebackground="#33A1FD")
        scale.pack(side="left", fill="x", expand=True, padx=5)

        var.trace_add("write", lambda *a: self._set_nested(key_path, var.get()))

    def _refresh_options_list(self):
        # Implementation for editing the 'options' list/dict
        # This can be complex, for now we just show a message
        tk.Label(self.options_frame, text="Use 'Code' tab for granular option editing.",
                 bg="#1e1e1e", fg="#666666", font=("Arial", 8, "italic")).pack(pady=5)

    def _on_save(self):
        if self.on_save:
            self.on_save(self.current_config)
        self.window.destroy()

    @staticmethod
    def launch(parent, config_data, on_save_callback):
        """API point for launching the bespoke editor."""
        return ButtonTogglerEditor(parent, config_data, on_save_callback)

if __name__ == "__main__":
    # Test standalone
    root = tk.Tk()
    root.withdraw()
    test_json = {
        "path": "test/button",
        "label": "Test Toggler",
        "layout": {"max_cols": 4, "corner_radius": 6},
        "bg_color": "#1a1a1a",
        "active_color": "#FF9900",
        "options": {"opt1": {"label": "One"}, "opt2": {"label": "Two"}}
    }
    def save_cb(data): print("SAVED:", json.dumps(data, indent=2))
    ButtonTogglerEditor.launch(root, test_json, save_cb)
    root.mainloop()
