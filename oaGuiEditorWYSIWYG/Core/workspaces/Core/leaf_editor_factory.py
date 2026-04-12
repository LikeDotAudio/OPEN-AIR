import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Core/leaf_editor_factory.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk, colorchooser
from ...state import state_manager

class LeafEditorFactory:
    """Spawns specialized editor widgets for leaf JSON properties."""

    @staticmethod
    def create(parent, key, value, full_path, source_instance, existing_widget=None):
        is_color = "color" in key.lower() or "colour" in key.lower() or (isinstance(value, str) and value.startswith("#") and len(value) in [4, 7])

        if is_color:
            editor = LeafEditorFactory._create_color_editor(parent, key, value, full_path, source_instance, existing_widget)
        else:
            editor = LeafEditorFactory._create_text_editor(parent, key, value, full_path, source_instance, existing_widget)
            
        return editor

    
    class _ColorEditorWidget(tk.Frame):
        def __init__(self, parent, key, value, full_path, source):
            super().__init__(parent, bg="#2b2b2b")
            self.key = key
            self.full_path = full_path
            self.source = source

            self.pack(fill="x", pady=2, padx=10)
            self.columnconfigure(0, weight=0)  # Label column
            self.columnconfigure(1, weight=1)  # Editor column

            tk.Label(self, text=f"{key}:", bg="#2b2b2b", fg="#cccccc", width=15, anchor="e").grid(row=0, column=0, sticky="e", padx=(0, 10))

            editor_frame = tk.Frame(self, bg="#2b2b2b")
            editor_frame.grid(row=0, column=1, sticky="we")

            bg_color = str(value).lower()
            if not bg_color.startswith("#"): bg_color = "#2b2b2b"

            self.swatch = tk.Canvas(editor_frame, width=25, height=18, bg=bg_color, highlightthickness=1, cursor="hand2")
            self.swatch.pack(side="left", padx=(0, 5))

            self.entry = ttk.Entry(editor_frame, style="Property.TEntry")
            self.entry.insert(0, str(value))
            self.entry.pack(side="left", fill="x", expand=True)

            self.swatch.bind("<Button-1>", self._pick_color)
            self.entry.bind("<Return>", self._update_state_from_entry)
            self.entry.bind("<FocusOut>", self._update_state_from_entry)

        def _pick_color(self, e):
            res = colorchooser.askcolor(title=f"Color: {self.key}", initialcolor=self.entry.get() or "#fff")
            if res[1]:
                self.set_value(res[1])
                state_manager.update_state(res[1], path=self.full_path, source=self.source)
        
        def _update_state_from_entry(self, e):
            current_value = self.entry.get()
            self.set_value(current_value)
            state_manager.update_state(current_value, path=self.full_path, source=self.source)

        def set_value(self, new_value):
            if not self.winfo_exists() or not self.entry.winfo_exists(): return
            if isinstance(new_value, str):
                self.entry.delete(0, tk.END)
                self.entry.insert(0, new_value)
                bg_color = new_value.lower()
                if not bg_color.startswith("#"): bg_color = "#2b2b2b"
                if self.swatch.winfo_exists():
                    self.swatch.config(bg=bg_color)

    @staticmethod
    def _create_color_editor(parent, key, value, full_path, source, existing_widget=None):
        if existing_widget and isinstance(existing_widget, LeafEditorFactory._ColorEditorWidget):
            existing_widget.set_value(value)
            return existing_widget
        return LeafEditorFactory._ColorEditorWidget(parent, key, value, full_path, source)

    
    class _TextEditorWidget(tk.Frame):
        def __init__(self, parent, key, value, full_path, source):
            super().__init__(parent, bg="#2b2b2b")
            self.key = key
            self.full_path = full_path
            self.source = source

            self.pack(fill="x", pady=2, padx=10) # Pack the main frame
            self.columnconfigure(0, weight=0)  # Label column
            self.columnconfigure(1, weight=1)  # Entry column
            
            self.lbl = tk.Label(self, text=f"{key}:", bg="#2b2b2b", fg="#cccccc", width=15, anchor="e")
            self.lbl.grid(row=0, column=0, sticky="e", padx=(0, 10))

            self.entry = ttk.Entry(self, style="Property.TEntry")
            self.entry.insert(0, str(value))
            self.entry.grid(row=0, column=1, sticky="we")

            self.entry.bind("<Return>", self._update_state_from_entry)
            self.entry.bind("<FocusOut>", self._update_state_from_entry)

            self.is_numeric = isinstance(value, (int, float))
            if self.is_numeric:
                self.lbl.config(cursor="sb_h_double_arrow")
                self.lbl.bind("<Button-1>", self._start_scrub)
                self.lbl.bind("<B1-Motion>", self._scrub)
                self.lbl.bind("<ButtonRelease-1>", self._stop_scrub)
                self.scrub_start_val = value
                self.scrub_start_x = 0

        def _update_state_from_entry(self, e):
            current_value_str = self.entry.get()
            try:
                new_value = current_value_str
                if self.is_numeric:
                    new_value = float(current_value_str) if isinstance(self.scrub_start_val, float) else int(current_value_str)
                state_manager.update_state(new_value, path=self.full_path, source=self.source)
                self.set_value(new_value)
            except ValueError:
                matrix_log("ui", "gui_builder", "LeafEditorFactory", f"Invalid numeric input: {current_value_str}", "WARNING")
                # Revert to last good value
                self.set_value(self.scrub_start_val)

        def _start_scrub(self, e):
            try:
                self.scrub_start_val = float(self.entry.get()) if '.' in self.entry.get() else int(self.entry.get())
                self.scrub_start_x = e.x_root
            except ValueError:
                self.scrub_start_val = 0

        def _scrub(self, e):
            delta = (e.x_root - self.scrub_start_x) // 2
            new_v = self.scrub_start_val + (delta * 0.1 if isinstance(self.scrub_start_val, float) else delta)
            self.set_value(new_v)
            state_manager.update_state(new_v, path=self.full_path, source=self.source)

        def _stop_scrub(self, e):
            pass

        def set_value(self, new_value):
            if not self.winfo_exists() or not self.entry.winfo_exists(): return
            
            value_to_set = new_value
            if self.is_numeric:
                try:
                    if isinstance(new_value, float):
                        value_to_set = f"{new_value:.3f}".rstrip('0').rstrip('.')
                    else:
                        value_to_set = str(int(new_value))
                except (ValueError, TypeError):
                    value_to_set = str(self.scrub_start_val)

            self.entry.delete(0, tk.END)
            self.entry.insert(0, str(value_to_set))

    @staticmethod
    def _create_text_editor(parent, key, value, full_path, source, existing_widget=None):
        if existing_widget and isinstance(existing_widget, LeafEditorFactory._TextEditorWidget):
            existing_widget.set_value(value)
            return existing_widget
        return LeafEditorFactory._TextEditorWidget(parent, key, value, full_path, source)

    @staticmethod
    def _bind_entry_focus(frame, entry, lbl, full_path, old_val, source):
        # This method seems to be obsolete with the new widget structure
        # but is kept for reference or future use if needed.
        pass
