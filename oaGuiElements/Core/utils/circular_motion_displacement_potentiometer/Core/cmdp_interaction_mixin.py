# Core/cmdp_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math

class CMDPInteractionMixin:
    """Handles canvas-level mouse and scroll interactions for the CMDP widget."""

    def on_click(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f:
            self.active_fader = f; f.dragging = True; f.lift()
            f.start_val, f.start_x, f.start_y = float(f.val_var.get()), e.x, e.y

    def on_drag(self, e):
        f = self.active_fader
        if f and f.dragging:
            from .cmdp_math import CircularMath
            if (e.state & 0x0008) or (e.state & 0x20000): # Alt
                f.angle_var.set(CircularMath.get_angle(e.x, e.y, self.center_x, self.center_y))
            else:
                proj = CircularMath.calculate_projection(e.x - f.start_x, e.y - f.start_y, float(f.angle_var.get()))
                f.val_var.set(max(0, min(100, f.start_val - (proj/f.track_len)*100)))
            self.update_tree(f)

    def on_mid_click(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f: self.active_fader = f; f.dragging = True

    def on_mid_drag(self, e):
        f = self.active_fader
        if f and f.dragging:
            f.angle_var.set(math.degrees(math.atan2(e.y-self.center_y, e.x-self.center_x)))
            self.update_tree(f)

    def on_release(self, e):
        if self.active_fader: self.active_fader.dragging = False; self.active_fader = None

    def on_motion(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f != self.hovered_fader:
            if self.hovered_fader: self.hovered_fader.set_hover(False)
            if f: f.set_hover(True); self.hovered_fader = f

    def on_scroll(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f:
            f.lift(); delta = 1 if (e.num == 4 or (hasattr(e, 'delta') and e.delta > 0)) else -1
            is_alt = (e.state & 0x0008) or (e.state & 0x20000)
            if is_alt: f.angle_var.set(float(f.angle_var.get()) + delta * 3)
            else: f.rot_var.set(max(0, min(100, float(f.rot_var.get()) + delta * 5)))
            self.update_tree(f)

    def get_fader_at(self, x, y):
        ids = self.canvas.find_closest(x, y, halo=20)
        if not ids: return None
        for t in self.canvas.gettags(ids[0]):
            if t.startswith("cmdp_fader_"):
                fid = int(t.split("_")[-1])
                return next((f for f in self.faders if f.widget_id == fid), None)
        return None
