# Core/dual_fader_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class DualFaderInteractionMixin:
    """Handles mouse click and drag input for the Dual Fader."""

    def _get_handle_under_mouse(self, x, y):
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        is_vert = self.orientation == "vertical"
        
        def get_dist(val):
            n = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            dn = n ** (1.0 / self.log_exponent)
            pos = (h if is_vert else w - 40.0) * (1.0 - dn if is_vert else dn) + 20.0
            return abs(y - pos) if is_vert else abs(x - pos)
            
        d1, d2 = get_dist(self.v1_var.get()), get_dist(self.v2_var.get())
        if d1 < 20 and d1 < d2: return "V1"
        if d2 < 20: return "V2"
        return None

    def _on_press(self, event):
        self.active_fader = self._get_handle_under_mouse(event.x, event.y)
        self._on_drag(event)

    def _on_drag(self, event):
        if not getattr(self, "active_fader", None): return
        
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        is_v = self.orientation == "vertical"
        
        norm = (event.y - 20.0) / (h - 40.0) if is_v else (event.x - 20.0) / (w - 40.0)
        if is_v: norm = 1.0 - norm
        
        val = self.min_val + (max(0, min(1, norm)) ** self.log_exponent) * (self.max_val - self.min_val)
        (self.v1_var if self.active_fader == "V1" else self.v2_var).set(val)
        
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/{self.active_fader}")
