# Core/trapezoid_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose


class TrapezoidInteractionMixin:
    """Handles mouse events (press, release, state toggle) for the Trapezoid Button."""

    def _on_press(self, event):
        self._is_pressed = True
        if not self.is_latching:
            self.variable.set(True)
        self._trigger_redraw()

    def _on_release(self, event):
        self._is_pressed = False
        if self.is_latching:
            self.variable.set(not self.variable.get())
        else:
            self.variable.set(False)
        self._trigger_redraw()
