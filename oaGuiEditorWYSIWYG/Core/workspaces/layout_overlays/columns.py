# layout_overlays/columns.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

def apply(layout, widget, path, is_focused, design_elements):
    """Handles Column highlighting (Thick Orange Border) using an overlay."""
    
    border = tk.Frame(widget.master, bg="orange", bd=0, highlightthickness=0)
    border._is_design_overlay = True
    design_elements.append(border)
    
    lbl = tk.Label(widget.master, text="COLUMN", bg="orange", fg="black", font=("Arial", 6, "bold"))
    lbl._is_design_overlay = True
    design_elements.append(lbl)

    def sync(x, y, w, h):
        if layout.show_columns.get() and path and (".fields" in path or path.endswith("fields")):
            th = 3
            border.place(x=x-th, y=y-th, width=w+(th*2), height=h+(th*2))
            border.lower(widget)
            lbl.place(x=x, y=y - 12)
        else:
            border.place_forget()
            lbl.place_forget()

    return sync
