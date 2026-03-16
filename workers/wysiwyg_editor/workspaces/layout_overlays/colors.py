# workers/wysiwyg_editor/workspaces/layout_overlays/colors.py
import tkinter as tk
from tkinter import colorchooser
from ...core.state import state

def apply(layout, widget, path, is_focused, design_elements):
    """Handles the 🎨 color palette button."""
    
    # 1. Setup Button
    color_btn = tk.Label(widget.master, text="🎨", bg="black", fg="white", font=("Arial", 8), cursor="hand2")
    color_btn._is_design_overlay = True
    design_elements.append(color_btn)
    
    color_btn.bind("<Button-1>", lambda e: _open_color_picker(layout, path))

    def sync(x, y, w, h):
        if layout.show_colors.get() and _has_color_properties(path):
            color_btn.place(x=x+20, y=y, width=20, height=20)
        else:
            color_btn.place_forget()

    return sync

def _has_color_properties(path):
    """Helper to check if a widget path contains any color settings."""
    data = state_manager.get_value_at_path(path)
    if not isinstance(data, dict): return False
    
    def _scan(d):
        for k, v in d.items():
            if "color" in k.lower() or "colour" in k.lower(): return True
            if isinstance(v, dict) and _scan(v): return True
        return False
    return _scan(data)

def _open_color_picker(layout, path):
    """Opens the OS color picker and updates the state."""
    color_key = "style.active_color"
    # Smart key detection
    if "cap_config" in path: color_key = path.replace("cap_config", "cap_color")
    elif "tick_config" in path: color_key = path.replace("tick_config", "tick_color")
    elif "value_config" in path: color_key = f"{path}.bg_color"
    elif "track_config" in path: color_key = f"{path}.bar_color"
    else: color_key = f"{path}.style.active_color"
    
    initial = state_manager.get_value_at_path(color_key) or "#FF9900"
    color = colorchooser.askcolor(title=f"Pick Color", initialcolor=initial)
    if color[1]: 
        state_manager.update_state(color[1], path=color_key, source=layout)
