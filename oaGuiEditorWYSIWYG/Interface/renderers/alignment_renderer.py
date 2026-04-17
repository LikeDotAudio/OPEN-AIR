# oaGuiEditorWYSIWYG/Interface/renderers/alignment_renderer.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular UI renderer for the Quick Alignment (Anchor) toolset.

import tkinter as tk

class AlignmentRenderer:
    """Renders the Quick Alignment (Anchor) button grid."""

    @staticmethod
    def render(container, align_str, on_set_align_callback):
        """
        Renders the alignment tools into the specified container.
        
        Args:
            container (tk.Widget): The parent frame to render into.
            align_str (str): The current alignment state (e.g. "left top").
            on_set_align_callback (callable): Function to call when a button is clicked.
        """
        tk.Label(container, text="QUICK ALIGNMENT (ANCHOR)", bg="#252525", fg="#888888", font=("Arial", 7, "bold")).pack()
        btn_frame = tk.Frame(container, bg="#252525")
        btn_frame.pack(pady=(5, 10))

        align = str(align_str).lower()
        buttons = {}

        for label in ["L", "R", "T", "B", "C"]:
            active = (label == "L" and "left" in align) or \
                     (label == "R" and "right" in align) or \
                     (label == "T" and "top" in align) or \
                     (label == "B" and "bottom" in align) or \
                     (label == "C" and not align)
                     
            btn = tk.Button(btn_frame, text=label, width=3, 
                            bg="#33A1FD" if active else "#444444", fg="white", 
                            relief="flat", font=("Arial", 8, "bold"), 
                            command=lambda l=label: on_set_align_callback(l))
            btn.pack(side="left", padx=2)
            buttons[label] = btn
            
        return buttons

    @staticmethod
    def update_highlights(buttons, align_str):
        """Updates button colors based on the current alignment state."""
        a = set(str(align_str).split())
        for l, b in buttons.items():
            active = (l=="L" and "left" in a) or \
                     (l=="R" and "right" in a) or \
                     (l=="T" and "top" in a) or \
                     (l=="B" and "bottom" in a) or \
                     (l=="C" and not a)
            b.config(bg="#33A1FD" if active else "#444444")
