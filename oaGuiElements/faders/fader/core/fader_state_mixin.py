import tkinter as tk

class FaderStateMixin:
    """Handles manual value entry, jump-to-reference, and MQTT bindings."""

    def _jump_to_reff_point(self, event):
        self.variable.set(self.reff_point)
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(
                self.path, 
                extra_payload={"SETTLED": True, "LOCKED": False}
            )

    def _open_manual_entry(self, event):
        if getattr(self, 'temp_entry', None) and self.temp_entry.winfo_exists(): return
        
        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        self.temp_entry.insert(0, str(self.variable.get()))
        self.temp_entry.select_range(0, tk.END)
        self.temp_entry.focus_set()
        
        self.temp_entry.bind("<Return>", self._submit_manual_entry)
        self.temp_entry.bind("<FocusOut>", self._submit_manual_entry)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    def _submit_manual_entry(self, event=None):
        try:
            val = float(self.temp_entry.get())
            if self.min_val <= val <= self.max_val:
                self.variable.set(val)
                if self.state_mirror_engine:
                    self.state_mirror_engine.broadcast_gui_change_to_mqtt(
                        self.path, 
                        extra_payload={"SETTLED": True, "LOCKED": False}
                    )
        except Exception:
            pass
        self._destroy_manual_entry()

    def _destroy_manual_entry(self, event=None):
        if getattr(self, 'temp_entry', None) and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None
