# Core/fader_bar_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

class FaderBarInteractionMixin:
    """Handles mouse and drag interactions for the composite fader."""

    def _on_press(self, event):
        self._on_drag(event)

    def _on_drag(self, event):
        val = self._get_val_from_y(event.y, self.draw_h, self.top_m)
        self.fader_var.set(max(self.min_val, min(self.max_val, val)))

    def _get_val_from_y(self, y, draw_h, y_offset=0):
        norm = 1.0 - ((y - y_offset) / draw_h); norm = max(0.0, min(1.0, norm))
        if self.log_exponent != 1.0: norm = norm ** self.log_exponent
        return self.min_val + (norm * (self.max_val - self.min_val))

    def _on_resize(self, event):
        if event.width > 5: self.width = event.width
        if event.height > 5: self.height = event.height
        self._draw_static(); self._draw_dynamic()
