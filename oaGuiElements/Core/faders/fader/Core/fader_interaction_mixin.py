# Core/fader_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import sys


class FaderInteractionMixin:
    """Handles all user input interactions for the fader (mouse drag, scroll wheel, clicks)."""

    def _start_interaction(self, event):
        self.is_sliding = True
        self.is_locked = True
        self._on_drag(event)

    def _on_drag(self, event):
        height = float(self.canvas.winfo_height())
        if height <= 1: return

        # Invert Y coordinate because Y increases downwards in Tkinter
        norm_y_inverted = (event.y - 25) / (height - 45)
        norm_y_inverted = max(0.0, min(1.0, norm_y_inverted))
        norm_pos = 1.0 - norm_y_inverted

        log_norm = max(0.0000001, norm_pos) ** self.log_exponent if self.log_exponent != 1.0 else norm_pos
        current_value = self.min_val + log_norm * (self.max_val - self.min_val)

        self.variable.set(current_value)
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(
                self.path,
                extra_payload={"SETTLED": False, "LOCKED": True}
            )

    def _stop_interaction(self, event):
        self.is_sliding = False
        self.is_locked = False
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(
                self.path,
                extra_payload={"SETTLED": True, "LOCKED": False}
            )
        if self.sync_callback:
            self.sync_callback()

    def _on_mousewheel(self, event):
        current_val = self.variable.get()
        val_range = self.max_val - self.min_val
        step = val_range * 0.05

        delta = 1 if (event.num == 4 or (hasattr(event, 'delta') and event.delta > 0)) else -1
        if sys.platform == "linux" and event.num == 5: delta = -1

        new_val = max(self.min_val, min(self.max_val, current_val + (delta * step)))

        self.is_sliding = True
        self.variable.set(new_val)

        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(
                self.path,
                extra_payload={"SETTLED": True, "LOCKED": False}
            )

        if hasattr(self.canvas, "winfo_exists") and self.canvas.winfo_exists():
            self.canvas.after(500, lambda: self._clear_sliding_state())

    def _clear_sliding_state(self):
        self.is_sliding = False
        if self.sync_callback:
            self.sync_callback()

    def _update_hover_state(self, hovering):
        self.is_hovered = hovering
        if self.canvas.find_withtag("track_slot"):
            col = self.track_hover_color if hovering else "#050505"
            self.canvas.itemconfig("track_slot", fill=col)
