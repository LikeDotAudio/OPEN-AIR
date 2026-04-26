# Core/gca_interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import sys


class GCAInteractionMixin:
    """Handles user interactions (Press, Drag, Mousewheel, Resize) for the GCA array."""

    def _on_press(self, event):
        self.start_y = event.y
        m_val = self._safe_get(self.master_value)
        cap_y = self._get_y_from_val(m_val)
        cap_h = 60
        draw_w = self.req_width
        offset_x = (self.width - draw_w) / 2 if self.width > draw_w else 0

        if (cap_y - cap_h/2) <= event.y <= (cap_y + cap_h/2):
            if getattr(self, 'mode', 'macro') == "micro":
                if offset_x <= event.x <= (offset_x + draw_w):
                    strip_w = draw_w / self.num_channels
                    col_idx = int((event.x - offset_x) / strip_w)
                    if 0 <= col_idx < self.num_channels:
                        self.dragging_child = col_idx
                        self.start_val = self._safe_get(self.child_values[col_idx])
                        return
            self.dragging_master = True
            self.start_val = m_val
        else:
            self.dragging_master = True
            self.start_val = self._get_val_from_y(event.y)
            new_v = max(self.min_val, min(self.max_val, self.start_val))
            self.master_value.set(new_v)
            if hasattr(self, 'path') and self.path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _on_drag(self, event):
        if getattr(self, 'dragging_master', False):
            new_val = self._get_val_from_y(event.y)
            new_val = max(self.min_val, min(self.max_val, new_val))
            self.master_value.set(new_val)
            if hasattr(self, 'path') and self.path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        elif getattr(self, 'dragging_child', -1) >= 0:
            dy = self.start_y - event.y
            val_range = self.max_val - self.min_val
            pixel_range = self.height - 40
            delta_val = (dy / pixel_range) * val_range
            new_val = max(self.min_val, min(self.max_val, self.start_val + delta_val))
            self.child_values[self.dragging_child].set(new_val)
            if hasattr(self, 'path') and self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch_{self.dragging_child+1}")

    def _on_release(self, event):
        self.dragging_master = False
        self.dragging_child = -1

    def _on_mousewheel(self, event):
        delta = 0
        if sys.platform == "linux":
            if event.num == 4: delta = 1
            elif event.num == 5: delta = -1
        else:
            delta = 1 if event.delta > 0 else -1
        if delta == 0: return

        current_val = self._safe_get(self.master_value)
        val_range = self.max_val - self.min_val
        step = val_range * 0.05
        new_val = max(self.min_val, min(self.max_val, current_val + (delta * step)))
        self.master_value.set(new_val)
        if hasattr(self, 'path') and self.path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _get_val_from_y(self, y):
        draw_h = self.height - 40
        norm = (draw_h - (y - 20)) / draw_h
        return self.min_val + (norm * (self.max_val - self.min_val))

    def _toggle_mode(self, event):
        self.mode = "micro" if getattr(self, 'mode', 'macro') == "macro" else "macro"
        self._draw()

    def _on_resize(self, event):
        if not hasattr(self, "_resize_timer"): self._resize_timer = None
        if self._resize_timer: self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(100, lambda: self._perform_resize(event.width, event.height))

    def _perform_resize(self, w, h):
        self._resize_timer = None
        if w > 1: self.width = w
        if h > 1: self.height = h
        self._draw()

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
