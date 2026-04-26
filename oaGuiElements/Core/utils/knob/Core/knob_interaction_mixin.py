# Core/knob_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import sys


class KnobInteractionMixin:
    """Handles all user input interactions for the rotary knob."""

    def _bind_knob_events(self):
        """Binds all input events to the Rotary Knob."""
        self.bind("<Configure>", self._on_resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_knob_press)
        self.bind("<B1-Motion>", self._on_knob_drag)
        self.bind("<ButtonRelease-1>", self._on_knob_release)
        self.bind("<Button-2>", self._jump_to_reff_point)
        self.bind("<Control-Button-1>", self._jump_to_reff_point)
        self.bind("<Alt-Button-1>", self._open_manual_entry)

    def _on_knob_press(self, event):
        self.state["start_y"] = event.y
        self.state["start_value"] = self.variable.get()
        self.is_locked = True

    def _on_knob_drag(self, event):
        if self.state.get("start_y") is None: return
        dy = self.state["start_y"] - event.y

        min_val, max_val = self.config["min"], self.config["max"]
        base_sensitivity = (max_val - min_val) / 200.0
        if self.config["fine_pitch"]:
            base_sensitivity /= 10.0

        if (event.state & 0x000C) == 0x000C:
            base_sensitivity /= 2.0

        delta = dy * base_sensitivity
        raw_new_val = self.state["start_value"] + delta

        if self.config["infinity"]:
             range_span = max_val - min_val
             new_val = min_val + ((raw_new_val - min_val) % range_span)
        else:
            new_val = max(min_val, min(max_val, raw_new_val))

        if self.variable.get() != new_val:
            self.variable.set(new_val)
            self._broadcast_cb()

    def _on_knob_release(self, event):
        self._broadcast_cb()
        self.state["start_y"] = None
        self.state["start_value"] = None
        self.is_locked = False

    def _on_mousewheel(self, event):
        current_val = self.variable.get()
        val_range = self.config["max"] - self.config["min"]
        step = val_range * 0.05
        delta = 0
        if sys.platform == "linux":
            delta = 1 if event.num == 4 else -1
        else:
            delta = 1 if event.delta > 0 else -1
        new_val = max(self.config["min"], min(self.config["max"], current_val + (delta * step)))
        self.variable.set(new_val)
        self._broadcast_cb()

    def _on_enter(self, event):
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)
        self.state["secondary_current"] = "#999999"
        self._draw_cb()

    def _on_leave(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.state["secondary_current"] = self.config["secondary_color"]
        self._draw_cb()

    def _on_resize(self, event):
        if self.state.get("_resize_timer"):
            self.safe_after_cancel(self.state["_resize_timer"])
        w, h = self.winfo_width(), self.winfo_height()
        self.state["_resize_timer"] = self.safe_after(100, lambda: self._perform_resize(w, h))

    def _perform_resize(self, w, h):
        self.state["_resize_timer"] = None
        if w > 1 and h > 1:
            if w != self.state["dims"]["w"] or h != self.state["dims"]["h"]:
                self.state["dims"]["w"], self.state["dims"]["h"] = w, h
                self._draw_cb()
