import tkinter as tk
import sys

class HorizontalFaderInteractionMixin:
    """Handles mouse, drag, scroll, and manual entry for the horizontal fader."""

    def _start_sliding(self, event):
        self.is_sliding = self.is_locked = True; self._on_drag(event)

    def _on_drag(self, event):
        ex, w = float(event.x), float(self.canvas.winfo_width())
        if w <= 1: w = self.width
        scale = float(self.config_data.get("fader_cap_scale", 1.0))
        px = int(float(self.config_data.get("cap_width", 50)) * scale) / 2.0 + 10.0
        if w <= (px * 2.0): return
        norm = max(0.0, min(1.0, (ex - px) / (w - (px * 2.0))))
        self.variable.set(self.min_val + (norm ** self.log_exponent) * (self.max_val - self.min_val))
        if self.path and self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _stop_sliding(self, event):
        if self.path and self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        self.is_sliding = self.is_locked = False; self._update_positions()

    def _on_mousewheel(self, event):
        delta = 1 if (event.num == 4 or (hasattr(event, 'delta') and event.delta > 0)) else -1
        if sys.platform == "linux" and event.num == 5: delta = -1
        new_val = max(self.min_val, min(self.max_val, self.variable.get() + (delta * (self.max_val-self.min_val)*0.05)))
        self.is_sliding = True; self.variable.set(new_val)
        if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        self.after(500, lambda: setattr(self, 'is_sliding', False) or self._update_positions())

    def _jump_to_reff_point(self, event):
        self.variable.set(self.reff_point)
        if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _open_manual_entry(self, event):
        if getattr(self, 'temp_entry', None): return
        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x, y=event.y); self.temp_entry.insert(0, str(self.variable.get()))
        self.temp_entry.focus_set()
        self.temp_entry.bind("<Return>", lambda e: self._submit_manual_entry())
        self.temp_entry.bind("<FocusOut>", lambda e: self._destroy_manual_entry())

    def _submit_manual_entry(self):
        try:
            v = float(self.temp_entry.get()); self.variable.set(max(self.min_val, min(self.max_val, v)))
            if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        except: pass
        self._destroy_manual_entry()

    def _destroy_manual_entry(self):
        if getattr(self, 'temp_entry', None): self.temp_entry.destroy(); self.temp_entry = None
