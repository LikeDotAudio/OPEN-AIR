# Managers/builder_layout_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1001.1
#
# Description: Manages resizing and layout synchronization for the Dynamic GUI Builder.

from .resize_throttler import throttle_resize_event
from .viewport_synchronizer import synchronize_viewport_dimensions

class BuilderLayoutManager:
    """Manages resizing and layout synchronization using atomic services."""
    def __init__(self, builder):
        self.builder = builder
        self._resize_timer = None
        self._last_w = 0
        self._last_h = 0

    def on_canvas_configure(self, event):
        """Reacts to physical window resizing via throttling service."""
        throttle_resize_event(self, event)

    def trigger_final_resize(self):
        """Throttled entry point that reads settled dimensions."""
        if not self.builder.winfo_exists(): return
        self.perform_canvas_resize(self.builder.winfo_width(), self.builder.winfo_height())

    def perform_canvas_resize(self, width, height):
        """Synchronizes dimensions via atomic service."""
        synchronize_viewport_dimensions(self, width, height)
