# workers/wysiwyg_editor/workspaces/layout_overlays/selection.py
import tkinter as tk
from ...core.event_bus import event_bus

def apply(layout, widget, path, is_focused, design_elements):
    """Handles the selection target (emoji) and focus highlight."""
    
    # 1. SELECTION HIGHLIGHT (Yellow Dotted via 4-Frame Construction)
    # Using 4 thin frames ensures the center is genuinely transparent 
    # and doesn't obscure the underlying widget on any platform.
    highlight_frames = []
    if is_focused:
        for _ in range(4):
            f = tk.Frame(widget.master, bg="yellow", bd=0, highlightthickness=0)
            f._is_design_overlay = True
            design_elements.append(f)
            highlight_frames.append(f)
    
    # 2. SELECTION HANDLE (🎯)
    try:
        master_bg = widget.master.cget("bg")
        if not master_bg: master_bg = "#2b2b2b"
    except:
        master_bg = "#2b2b2b"

    bg_color = "#33A1FD" if is_focused else master_bg
    sel_overlay = tk.Label(widget.master, text="🎯", bg=bg_color, fg="white", font=("Arial", 8), cursor="hand2")
    sel_overlay._is_design_overlay = True
    design_elements.append(sel_overlay)

    def _on_click(event):
        new_path = None if is_focused else path
        layout._on_widget_focused(new_path)

    sel_overlay.bind("<Button-1>", _on_click)
    
    # Also bind to the widget itself to make selection easier
    widget.bind("<Button-1>", _on_click, add="+")
    
    def _on_enter(e): sel_overlay.config(bg="#FF00FF")
    def _on_leave(e): sel_overlay.config(bg="#33A1FD" if is_focused else master_bg)
    sel_overlay.bind("<Enter>", _on_enter)
    sel_overlay.bind("<Leave>", _on_leave)

    def sync(x, y, w, h):
        if highlight_frames:
            # Thickness of the selection border
            th = 2 
            # Top
            highlight_frames[0].place(x=x-th, y=y-th, width=w+(th*2), height=th)
            # Bottom
            highlight_frames[1].place(x=x-th, y=y+h, width=w+(th*2), height=th)
            # Left
            highlight_frames[2].place(x=x-th, y=y, width=th, height=h)
            # Right
            highlight_frames[3].place(x=x+w, y=y, width=th, height=h)
            
        sel_overlay.place(x=x, y=y, width=20, height=20)

    return sync
