# layout_overlays/selection.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaComBroker.Core.event_bus import event_bus
from ...Core.state import state_manager
from ..layout_engine.snap_logic import snap_to_grid

def apply_design_overlay(layout, widget, path, is_focused, design_elements):
    """Handles the selection target (emoji), focus highlight, and interactive handles."""
    
    # 1. SELECTION HIGHLIGHT (Yellow Dotted via 4-Frame Construction)
    highlight_frames = []
    if is_focused:
        for _ in range(4):
            f = tk.Frame(widget.master, bg="yellow", bd=0, highlightthickness=0)
            f._is_design_overlay = True
            design_elements.append(f)
            highlight_frames.append(f)
    
    # 2. SELECTION HANDLE (🎯) - Acts as a MOVE handle
    try:
        master_bg = widget.master.cget("bg")
        if not master_bg: master_bg = "#2b2b2b"
    except:
        master_bg = "#2b2b2b"

    bg_color = "#33A1FD" if is_focused else master_bg
    move_handle = tk.Label(widget.master, text="🎯", bg=bg_color, fg="white", font=("Arial", 8), cursor="fleur")
    move_handle._is_design_overlay = True
    design_elements.append(move_handle)

    # 3. RESIZE HANDLES (Bottom-Right)
    resize_handle = None
    if is_focused:
        resize_handle = tk.Frame(widget.master, bg="#00FF00", width=10, height=10, cursor="bottom_right_corner")
        resize_handle._is_design_overlay = True
        design_elements.append(resize_handle)

    # --- INTERACTION LOGIC ---
    drag_data = {"x": 0, "y": 0, "orig_x": 0, "orig_y": 0, "orig_w": 0, "orig_h": 0}

    def _start_drag(event):
        drag_data["x"] = event.x_root
        drag_data["y"] = event.y_root
        # Extract current state geometry
        full_state = state_manager.get_state()
        # Navigate to component in state (this is simplified, needs robust path resolver)
        # For now, we'll assume the path is correct and we can update it.
        pass

    def _on_move_drag(event):
        dx = event.x_root - drag_data["x"]
        dy = event.y_root - drag_data["y"]
        # In a real implementation, we'd update a preview overlay here
        pass

    def _on_move_release(event):
        # Apply Snap-to-Grid on release and update State
        dx = event.x_root - drag_data["x"]
        dy = event.y_root - drag_data["y"]
        
        # Get current geometry from state
        # This is a placeholder for the actual path-based update logic
        # state_manager.update_state(new_val, path=f"{path}.geometry.x")
        pass

    def _on_click(event):
        new_path = None if is_focused else path
        layout._on_widget_focused(new_path)

    move_handle.bind("<Button-1>", _on_click)
    widget.bind("<Button-1>", _on_click, add="+")
    
    def _on_enter(e): move_handle.config(bg="#FF00FF")
    def _on_leave(e): move_handle.config(bg="#33A1FD" if is_focused else master_bg)
    move_handle.bind("<Enter>", _on_enter)
    move_handle.bind("<Leave>", _on_leave)

    def sync(x, y, w, h):
        if highlight_frames:
            th = 2 
            highlight_frames[0].place(x=x-th, y=y-th, width=w+(th*2), height=th)
            highlight_frames[1].place(x=x-th, y=y+h, width=w+(th*2), height=th)
            highlight_frames[2].place(x=x-th, y=y, width=th, height=h)
            highlight_frames[3].place(x=x+w, y=y, width=th, height=h)
            
        move_handle.place(x=x, y=y, width=20, height=20)
        if resize_handle:
            resize_handle.place(x=x+w-5, y=y+h-5, width=10, height=10)

    return sync
