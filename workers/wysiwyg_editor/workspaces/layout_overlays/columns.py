# workers/wysiwyg_editor/workspaces/layout_overlays/columns.py
import tkinter as tk

def apply(layout, widget, path, is_focused, design_elements):
    """Handles Column highlighting (Thick Dotted Orange Border)."""
    
    if layout.show_columns.get() and path:
        # Heuristic: containers with '.fields' are structural columns/containers
        if ".fields" in path or path.endswith("fields"):
            try:
                # 1. Background highlight
                widget.config(highlightbackground="orange", highlightthickness=3)
                
                # 2. COLUMN tag
                lbl = tk.Label(widget.master, text="COLUMN", bg="orange", fg="black", font=("Arial", 6, "bold"))
                lbl._is_design_overlay = True
                design_elements.append(lbl)
                
                def sync(x, y, w, h):
                    lbl.place(x=x, y=y - 12)
                return sync
                
            except tk.TclError: pass

    def sync(x, y, w, h):
        pass
    return sync
