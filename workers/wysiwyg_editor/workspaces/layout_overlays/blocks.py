# workers/wysiwyg_editor/workspaces/layout_overlays/blocks.py
import tkinter as tk

def apply(layout, widget, path, is_focused, design_elements):
    """Handles tiered block shading."""
    
    if layout.show_blocks.get() and path:
        if ".fields." in path:
            # Nested Fields - Darker Shade
            try: widget.config(bg="#1a1a1a") 
            except tk.TclError: pass
        else:
            # Root Block - Base Shade
            try: widget.config(bg="#3a3a3a")
            except tk.TclError: pass
    else:
        # Restore default shade
        try: widget.config(bg="#2b2b2b")
        except tk.TclError: pass

    def sync(x, y, w, h):
        pass

    return sync
