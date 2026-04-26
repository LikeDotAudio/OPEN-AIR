# oaGuiEditorWYSIWYG/Interface/renderers/section_renderer.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular UI renderer for property sections and collapsible headers.

import tkinter as tk


class SectionRenderer:
    """Renders collapsible section headers for the property tree."""

    @staticmethod
    def render(parent, key, full_path, is_virtual, is_expanded_val, on_toggle_callback, on_add_callback, message_callback=None):
        """
        Renders a section header with expansion toggle and optional add button.
        If message_callback is provided, shows a message emoji to view details.
        """
        h_frame = tk.Frame(parent, bg="#2d2d2d", pady=2)
        h_frame.pack(fill="x", pady=(8, 2))

        is_expanded = tk.BooleanVar(value=is_expanded_val)
        fg_col = "#33A1FD" if not is_virtual else "#666666"
        toggle_char = "▼" if is_expanded_val else "▶"

        title_lbl = tk.Label(h_frame, text=f"{toggle_char} {key.upper()}", bg="#2d2d2d", fg=fg_col,
                             font=("Arial", 8, "bold"), cursor="hand2", anchor="w")
        title_lbl.pack(side="left", fill="x", expand=True)

        if message_callback:
            msg_btn = tk.Label(h_frame, text="✉️", bg="#2d2d2d", fg="#FF9900", font=("Arial", 10), cursor="hand2")
            msg_btn.pack(side="right", padx=5)
            msg_btn.bind("<Button-1>", lambda e: message_callback())

        if is_virtual:
            tk.Button(h_frame, text="+", bg="#37373d", fg="#aaaaaa", relief="flat", font=("Arial", 7, "bold"),
                      command=on_add_callback).pack(side="right", padx=5)

        def toggle_wrapper(e):
            new_state = not is_expanded.get()
            is_expanded.set(new_state)
            char = "▼" if new_state else "▶"
            title_lbl.config(text=f"{char} {key.upper()}")
            on_toggle_callback(new_state)

        title_lbl.bind("<Button-1>", toggle_wrapper)

        return h_frame, is_expanded
