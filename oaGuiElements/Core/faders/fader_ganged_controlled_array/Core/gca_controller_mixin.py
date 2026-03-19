import tkinter as tk

class GCAControllerMixin:
    """Handles synchronization logic for ganged faders (Master/Child sync)."""

    def _calculate_master_average(self):
        total = sum([self._safe_get(v) for v in self.child_values])
        return total / len(self.child_values) if self.child_values else self.min_val

    def _recalculate_offsets(self):
        m_val = self._safe_get(self.master_value)
        for i in range(self.num_channels):
            self.child_offsets[i] = self._safe_get(self.child_values[i]) - m_val

    def _update_children_from_master(self, broadcast=True):
        m_val = self._safe_get(self.master_value)
        for i in range(self.num_channels):
            new_val = m_val + self.child_offsets[i]
            new_val = max(self.min_val, min(self.max_val, new_val))
            if abs(self._safe_get(self.child_values[i]) - new_val) > 0.001:
                self.child_values[i].set(new_val)
                if broadcast and hasattr(self, 'path') and self.path:
                    self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch_{i+1}")

    def _update_master_from_children(self, broadcast=True):
        new_master = self._calculate_master_average()
        if abs(self._safe_get(self.master_value) - new_master) > 0.001:
            self.master_value.set(new_master)
            if broadcast and hasattr(self, 'path') and self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _on_master_var_change(self, *args):
        if getattr(self, '_lock_sync', False): return
        self._lock_sync = True
        self._update_children_from_master(broadcast=False) 
        self._lock_sync = False
        self._draw()

    def _on_child_var_change(self, idx, *args):
        if getattr(self, '_lock_sync', False): return
        self._lock_sync = True
        self._update_master_from_children(broadcast=False)
        self._recalculate_offsets()
        self._lock_sync = False
        self._draw()

    def _safe_get(self, var):
        try:
            val = var.get()
            if isinstance(val, str) and val.strip() == "": return self.min_val
            return float(val)
        except (tk.TclError, ValueError, TypeError): return self.min_val
