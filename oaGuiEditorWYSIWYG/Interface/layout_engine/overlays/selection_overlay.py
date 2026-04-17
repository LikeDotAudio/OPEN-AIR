# oaGuiEditorWYSIWYG/Interface/layout_engine/overlays/selection_overlay.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular Selection Highlight and Move Handle.

import tkinter as tk
from .base_overlay import BaseOverlay

class SelectionOverlay(BaseOverlay):
    """Handles selection markers and the primary move/focus handle."""

    def __init__(self, workspace, widget, path, is_focused):
        super().__init__(workspace, widget, path, is_focused)
        self._build_ui()

    def _build_ui(self):
        # 1. 4-Frame Construction for yellow selection highlight
        self.highlight_frames = []
        if self.is_focused:
            for _ in range(4):
                f = self.create_element(tk.Frame, bg="yellow", bd=0, highlightthickness=0)
                self.highlight_frames.append(f)

        # 2. RESIZE HANDLES (Bottom-Right) - Visual only
        self.resize_marker = None
        if self.is_focused:
            self.resize_marker = self.create_element(tk.Frame, bg="#00FF00", width=10, height=10, cursor="bottom_right_corner")

        # 3. SELECTION HANDLE (🎯)
        master_bg = "#2b2b2b"
        try: master_bg = self.widget.master.cget("bg")
        except: pass

        bg_color = "#33A1FD" if self.is_focused else master_bg
        self.move_handle = self.create_element(tk.Label, text="🎯", bg=bg_color, fg="white", font=("Arial", 8), cursor="fleur")
        
        # 4. EVENT BINDINGS
        self.move_handle.bind("<Button-1>", self._on_click)
        self.widget.bind("<Button-1>", self._on_click, add="+")
        
        self.move_handle.bind("<Enter>", lambda e: self.move_handle.config(bg="#FF00FF"))
        self.move_handle.bind("<Leave>", lambda e: self.move_handle.config(bg="#33A1FD" if self.is_focused else master_bg))

    def _on_click(self, event):
        new_path = None if self.is_focused else self.path
        self.workspace._on_widget_focused(new_path)

    def sync(self, x, y, w, h):
        if self.highlight_frames:
            th = 2 
            self.highlight_frames[0].place(x=x-th, y=y-th, width=w+(th*2), height=th)
            self.highlight_frames[1].place(x=x-th, y=y+h, width=w+(th*2), height=th)
            self.highlight_frames[2].place(x=x-th, y=y, width=th, height=h)
            self.highlight_frames[3].place(x=x+w, y=y, width=th, height=h)
            
        self.move_handle.place(x=x, y=y, width=20, height=20)
        if self.resize_marker:
            self.resize_marker.place(x=x+w-5, y=y+h-5, width=10, height=10)
