# Managers/builder_layout_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Manages resizing and layout synchronization for the Dynamic GUI Builder.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
from oaGui.Constants.builder_constants import RESIZE_THROTTLE_DELAY, RESIZE_WIDTH_THRESHOLD

class BuilderLayoutManager:
    """Manages resizing and layout synchronization for the Dynamic GUI Builder."""
    def __init__(self, builder):
        self.builder = builder
        self._resize_timer = None
        self._last_w = 0
        self._last_h = 0

    def on_canvas_configure(self, event):
        """Reacts to physical window resizing with threshold-based throttling."""
        if event.widget != self.builder: return
        if getattr(self.builder, '_is_rebuilding', False): return

        w, h = event.width, event.height

        if abs(w - self._last_w) < RESIZE_WIDTH_THRESHOLD and abs(h - self._last_h) < RESIZE_WIDTH_THRESHOLD:
            return

        self._last_w = w
        self._last_h = h

        if self._resize_timer: self.builder.after_cancel(self._resize_timer)
        self._resize_timer = self.builder.after(RESIZE_THROTTLE_DELAY, self.trigger_final_resize)
        
        if getattr(self.builder, 'is_editor', False):
            from oaGuiEditorWYSIWYG.Methods.builder_editor_grid import BuilderEditorGrid
            self.builder.after(RESIZE_THROTTLE_DELAY + 10, 
                               lambda: BuilderEditorGrid.draw(self.builder.canvas, self.builder.scroll_frame, True))

    def trigger_final_resize(self):
        """Throttled entry point that reads settled dimensions."""
        if not self.builder.winfo_exists(): return
        self.perform_canvas_resize(self.builder.winfo_width(), self.builder.winfo_height())

    def perform_canvas_resize(self, width, height):
        """Calculates and applies new dimensions to the canvas and inner frame."""
        self._resize_timer = None
        if width <= 1 or height <= 1 or not self.builder.canvas_window_id: return

        req_w = self.builder.scroll_frame.winfo_reqwidth()
        req_h = self.builder.scroll_frame.winfo_reqheight()

        new_w = width if not self.builder.allow_horizontal_scroll else max(width, req_w)
        new_h = max(height, req_h)
        
        matrix_log("ui", "gui_render", "perform_canvas_resize", 
                   f"📏 [BUILDER_SIZE] Tab: {getattr(self.builder, 'tab_name', '??')} | "
                   f"Viewport: {width}x{height} | Content: {req_w}x{req_h} | Target: {new_w}x{new_h}", "TRACE")

        if hasattr(self.builder, 'footer') and self.builder.footer:
            self.builder.footer.update_dimensions(width, height, req_w, req_h)

        if new_w <= 1 or new_h <= 1: return

        try:
            self.builder.canvas.itemconfig(self.builder.canvas_window_id, width=int(new_w), height=int(new_h))
            if hasattr(self.builder, '_trigger_background_sync'):
                self.builder._trigger_background_sync(force=True)
        except tk.TclError: pass
