# oaGuiEditorWYSIWYG/Interface/renderers/info_renderer.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular UI renderer for informational elements (Lists, Virtual Leaves).

import tkinter as tk


class InfoRenderer:
    """Renders informational UI elements for lists and non-existent properties."""

    @staticmethod
    def render_list(parent, key, value):
        """Renders a summary frame for list-type data."""
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#888888", width=15, anchor="e").pack(side="left")
        list_text = f"[List: {len(value)} items]"
        tk.Label(f, text=list_text, bg="#2b2b2b", fg="#666666").pack(side="left", padx=10)
        return f

    @staticmethod
    def render_virtual_leaf(parent, key, value, on_add_callback):
        """Renders a placeholder for properties that can be added to the state."""
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#555555", width=15, anchor="e").pack(side="left")

        tk.Button(f, text="+ ADD", bg="#3a3a3a", fg="#aaaaaa", relief="flat", font=("Arial", 7, "bold"),
                  command=on_add_callback).pack(side="left", padx=10)

        tk.Label(f, text=f"({value})", bg="#2b2b2b", fg="#444444", font=("Arial", 7, "italic")).pack(side="left")
        return f
