# layout_overlays/structure.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

def apply_design_overlay(layout, widget, path, is_focused, design_elements):
    """Handles the basic structure outline (#444444 border) using an overlay."""
    
    border = tk.Frame(widget.master, bg="#444444", bd=0, highlightthickness=0)
    border._is_design_overlay = True
    design_elements.append(border)

    def sync(x, y, w, h):
        if layout.show_structure.get():
            # Create a 1px border by placing behind or around
            # We'll place it slightly larger than the widget
            th = 1
            border.place(x=x-th, y=y-th, width=w+(th*2), height=h+(th*2))
            border.lower(widget) # Ensure it stays behind functional elements
        else:
            border.place_forget()

    return sync
