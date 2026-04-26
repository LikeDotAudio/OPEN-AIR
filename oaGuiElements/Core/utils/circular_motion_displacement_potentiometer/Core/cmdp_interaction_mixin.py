# Core/cmdp_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math


class CMDPInteractionMixin:
    """Handles canvas-level mouse and scroll interactions for the CMDP widget."""

    def on_click(self, e):
        active_fader = self.get_fader_at(e.x, e.y)
        if active_fader:
            self.active_fader = active_fader; active_fader.dragging = True; active_fader.lift()
            active_fader.start_val, active_fader.start_x, active_fader.start_y = float(active_fader.val_var.get()), e.x, e.y

    def on_drag(self, e):
        active_fader = self.active_fader
        if active_fader and active_fader.dragging:
            from .cmdp_math import CircularMath
            if (e.state & 0x0008) or (e.state & 0x20000): # Alt
                active_fader.angle_var.set(CircularMath.get_angle(e.x, e.y, self.center_x, self.center_y))
            else:
                proj = CircularMath.calculate_projection(e.x - active_fader.start_x, e.y - active_fader.start_y, float(active_fader.angle_var.get()))
                active_fader.val_var.set(max(0, min(100, active_fader.start_val - (proj/active_fader.track_len)*100)))
            self.update_tree(active_fader)

    def on_mid_click(self, e):
        active_fader = self.get_fader_at(e.x, e.y)
        if active_fader: self.active_fader = active_fader; active_fader.dragging = True

    def on_mid_drag(self, e):
        active_fader = self.active_fader
        if active_fader and active_fader.dragging:
            active_fader.angle_var.set(math.degrees(math.atan2(e.y-self.center_y, e.x-self.center_x)))
            self.update_tree(active_fader)

    def on_release(self, e):
        if self.active_fader: self.active_fader.dragging = False; self.active_fader = None

    def on_motion(self, e):
        active_fader = self.get_fader_at(e.x, e.y)
        if active_fader != self.hovered_fader:
            if self.hovered_fader: self.hovered_fader.set_hover(False)
            if active_fader: active_fader.set_hover(True); self.hovered_fader = active_fader

    def on_scroll(self, e):
        active_fader = self.get_fader_at(e.x, e.y)
        if active_fader:
            active_fader.lift(); delta = 1 if (e.num == 4 or (hasattr(e, 'delta') and e.delta > 0)) else -1
            is_alt = (e.state & 0x0008) or (e.state & 0x20000)
            if is_alt: active_fader.angle_var.set(float(active_fader.angle_var.get()) + delta * 3)
            else: active_fader.rot_var.set(max(0, min(100, float(active_fader.rot_var.get()) + delta * 5)))
            self.update_tree(active_fader)

    def get_fader_at(self, x, y):
        ids = self.canvas.find_closest(x, y, halo=20)
        if not ids: return None
        for t in self.canvas.gettags(ids[0]):
            if t.startswith("cmdp_fader_"):
                fid = int(t.split("_")[-1])
                return next((f for f in self.faders if f.widget_id == fid), None)
        return None
