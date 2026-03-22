# Core/ltp_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

class LTPInteractionMixin:
    """Handles mouse and drag interactions for the Linear Travelling Potentiometer."""

    def _setup_drag_state(self):
        self.drag_state = {"active": False, "start_x": 0, "start_y": 0, "start_lin": 0, "start_rot": 0, "is_ctrl": False}

    def on_press(self, event, canvas):
        w, h = canvas.winfo_width(), canvas.winfo_height()
        h_pos = self._get_handle_pos(h if self.orientation == "vertical" else w)
        r = self.cap_radius
        
        if self.orientation == "vertical": in_zone = (w/2-r <= event.x <= w/2+r) and (h_pos-r <= event.y <= h_pos+r)
        else: in_zone = (h_pos-r <= event.x <= h_pos+r) and (h/2-r <= event.y <= h/2+r)
        
        if not in_zone: self._set_linear_from_event(event, w, h)
        
        self.drag_state.update({"active": True, "start_x": event.x, "start_y": event.y, "start_lin": self.linear_var.get(), "start_rot": self.rotation_var.get(), "is_ctrl": bool(event.state & 0x0004)})
        self.is_sliding = True

    def on_drag(self, event, canvas):
        if not self.drag_state["active"]: return
        w, h = canvas.winfo_width(), canvas.winfo_height()
        ctrl = bool(event.state & 0x0004)
        
        if ctrl != self.drag_state["is_ctrl"]:
            self.drag_state.update({"start_x": event.x, "start_y": event.y, "start_lin": self.linear_var.get(), "start_rot": self.rotation_var.get(), "is_ctrl": ctrl})
        
        dx, dy = event.x - self.drag_state["start_x"], event.y - self.drag_state["start_y"]
        flen = (h if self.orientation == "vertical" else w) - 50
        mult = 2.0 if (self.freestyle and ctrl) else 1.0

        if self.orientation == "vertical":
            if self.freestyle or ctrl:
                new_rot = self.drag_state["start_rot"] + (dx / (flen/2)) * 100 * mult
                self.rotation_var.set(max(self.rotation_min, min(self.rotation_max, new_rot)))
            if self.freestyle or not ctrl:
                new_lin = self.drag_state["start_lin"] - (dy / flen) * (self.max_val - self.min_val)
                self.linear_var.set(max(self.min_val, min(self.max_val, new_lin)))
        else:
            if self.freestyle or ctrl:
                new_rot = self.drag_state["start_rot"] - (dy / (h/2)) * 100 * mult
                self.rotation_var.set(max(self.rotation_min, min(self.rotation_max, new_rot)))
            if self.freestyle or not ctrl:
                new_lin = self.drag_state["start_lin"] + (dx / flen) * (self.max_val - self.min_val)
                self.linear_var.set(max(self.min_val, min(self.max_val, new_lin)))

        self._broadcast_changes()

    def _set_linear_from_event(self, event, w, h):
        norm = 1.0 - (event.y - 25) / (h - 50) if self.orientation == "vertical" else (event.x - 25) / (w - 50)
        norm = max(0.0, min(1.0, norm))
        self.linear_var.set(self.min_val + (norm ** self.log_exponent) * (self.max_val - self.min_val))
        self._broadcast_changes(only_linear=True)

    def _broadcast_changes(self, only_linear=False):
        if self.path and self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
            if not only_linear: self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}.rotation")
