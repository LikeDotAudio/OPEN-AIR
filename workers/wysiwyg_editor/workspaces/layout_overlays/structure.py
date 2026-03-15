# workers/wysiwyg_editor/workspaces/layout_overlays/structure.py
import tkinter as tk

def apply(layout, widget, path, is_focused, design_elements):
    """Handles the basic structure outline (#444444 border)."""
    
    if layout.show_structure.get():
        try: 
            widget.config(highlightbackground="#444444", highlightthickness=1)
        except tk.TclError: pass
    else:
        try: 
            widget.config(highlightthickness=0)
        except tk.TclError: pass

    def sync(x, y, w, h):
        pass # No extra design elements to position

    return sync
