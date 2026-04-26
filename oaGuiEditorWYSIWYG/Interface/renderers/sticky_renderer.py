# oaGuiEditorWYSIWYG/Interface/renderers/sticky_renderer.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular UI renderer for the Quick Sticky (Stretch) toolset.

import tkinter as tk


class StickyRenderer:
    """Renders the Quick Sticky (Stretch) button presets."""

    @staticmethod
    def render(container, stretch_str, on_set_sticky_callback):
        """
        Renders the sticky tools into the specified container.
        
        Args:
            container (tk.Widget): The parent frame to render into.
            stretch_str (str): The current stretch state (e.g. "width").
            on_set_sticky_callback (callable): Function to call when a button is clicked.
        """
        tk.Label(container, text="QUICK STICKY (STRETCH)", bg="#252525", fg="#888888", font=("Arial", 7, "bold")).pack()
        btn_frame = tk.Frame(container, bg="#252525")
        btn_frame.pack(pady=5)

        stretch = str(stretch_str).lower()
        buttons = {}

        presets = [("EW", "width"), ("NS", "height"), ("NSEW", "both"), ("NONE", "")]
        for label, value in presets:
            active = (value in stretch) or (label == "NONE" and not stretch)
            btn = tk.Button(btn_frame, text=label, width=5,
                            bg="#2ecc71" if active else "#444444", fg="white",
                            relief="flat", font=("Arial", 7, "bold"),
                            command=lambda v=value: on_set_sticky_callback(v))
            btn.pack(side="left", padx=2)
            buttons[label] = btn

        return buttons

    @staticmethod
    def update_highlights(buttons, stretch_str):
        """Updates button colors based on the current stretch state."""
        s = set(str(stretch_str).split())
        for l, b in buttons.items():
            active = (l=="EW" and ("width" in s or "both" in s)) or \
                     (l=="NS" and ("height" in s or "both" in s)) or \
                     (l=="NSEW" and "both" in s) or \
                     (l=="NONE" and not s)
            b.config(bg="#2ecc71" if active else "#444444")
