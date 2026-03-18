# workers/wysiwyg_editor/workspaces/layout_overlays/blocks.py
import tkinter as tk

def apply(layout, widget, path, is_focused, design_elements):
    """Handles tiered block shading using a background overlay."""
    
    bg_overlay = tk.Frame(widget.master, bd=0, highlightthickness=0)
    bg_overlay._is_design_overlay = True
    design_elements.append(bg_overlay)

    def sync(x, y, w, h):
        if layout.show_blocks.get() and path:
            if ".fields." in path:
                # Nested Fields - Darker Shade
                bg_overlay.config(bg="#1a1a1a") 
            else:
                # Root Block - Base Shade
                bg_overlay.config(bg="#3a3a3a")
            
            bg_overlay.place(x=x, y=y, width=w, height=h)
            bg_overlay.lower(widget) # Stay behind functional element
        else:
            bg_overlay.place_forget()

    return sync
