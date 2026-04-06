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

            self.pack(fill="x", pady=2) # This frame contains the swatch and entry

            bg_color = str(value).lower()
            if not bg_color.startswith("#"): bg_color = "#2b2b2b" # Default for invalid colors

            self.swatch = tk.Canvas(self, width=25, height=18, bg=bg_color, highlightthickness=1, cursor="hand2")
            self.swatch.pack(side="left", padx=(10, 5))

            self.entry = ttk.Entry(self, style="Property.TEntry")
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
            self.set_value(current_value) # Update internal swatch too
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
            # Add validation or error handling for invalid new_value types

    @staticmethod
    def _create_color_editor(parent, key, value, full_path, source, existing_widget=None):
        if existing_widget and isinstance(existing_widget, LeafEditorFactory._ColorEditorWidget):
            existing_widget.set_value(value)
            return existing_widget
        else:
            return LeafEditorFactory._ColorEditorWidget(parent, key, value, full_path, source)

    
    class _TextEditorWidget(tk.Frame):
        def __init__(self, parent, key, value, full_path, source): # Removed lbl
            super().__init__(parent, bg="#2b2b2b")
            self.key = key
            self.full_path = full_path
            self.source = source
            
            # Create the label internally
            self.lbl = tk.Label(self, text=f"{key}:", bg="#2b2b2b", fg="#cccccc", width=15, anchor="e")
            self.lbl.pack(side="left")

            self.pack(side="left", fill="x", expand=True, padx=(10, 0)) # This frame contains the entry

            self.entry = ttk.Entry(self, style="Property.TEntry")
            self.entry.insert(0, str(value))
            self.entry.pack(side="left", fill="x", expand=True)

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
                if self.is_numeric:
                    new_value = float(current_value_str) if isinstance(self.scrub_start_val, float) else int(current_value_str)
                else:
                    new_value = current_value_str
                state_manager.update_state(new_value, path=self.full_path, source=self.source)
            except ValueError:
                matrix_log("ui", "gui_builder", "LeafEditorFactory", f"Invalid numeric input: {current_value_str}", "WARNING")
            self.set_value(new_value) # Ensure entry and internal state are consistent

        def _start_scrub(self, e):
            self.scrub_start_val = float(self.entry.get()) if isinstance(self.scrub_start_val, float) else int(self.entry.get())
            self.scrub_start_x = e.x_root

        def _scrub(self, e):
            delta = (e.x_root - self.scrub_start_x) // 2
            new_v = self.scrub_start_val + (delta * 0.1 if isinstance(self.scrub_start_val, float) else delta)
            self.set_value(new_v)
            # Update state continuously during scrub
            state_manager.update_state(new_v, path=self.full_path, source=self.source)

        def _stop_scrub(self, e):
            # Final state update already handled by _scrub
            pass

        def set_value(self, new_value):
            if not self.winfo_exists() or not self.entry.winfo_exists(): return
            if self.is_numeric:
                if isinstance(new_value, float):
                    formatted_value = f"{new_value:.3f}".rstrip('0').rstrip('.')
                else:
                    formatted_value = str(int(new_value))
                self.entry.delete(0, tk.END)
                self.entry.insert(0, formatted_value)
            else:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, str(new_value))
            # Add validation or error handling for invalid new_value types

    @staticmethod
    def _create_text_editor(parent, key, value, full_path, source, existing_widget=None): # Removed lbl
        if existing_widget and isinstance(existing_widget, LeafEditorFactory._TextEditorWidget):
            existing_widget.set_value(value)
            return existing_widget
        else:
            return LeafEditorFactory._TextEditorWidget(parent, key, value, full_path, source) # Removed lbl

    @staticmethod
    def _bind_entry_focus(frame, entry, lbl, full_path, old_val, source):
        def focus_in(e): frame.config(bg="#444444"); 
        if lbl: lbl.config(bg="#444444", fg="#33A1FD")
        
        def focus_out(e):
            frame.config(bg="#2b2b2b"); 
            if lbl: lbl.config(bg="#2b2b2b", fg="#cccccc")
            v = entry.get()
            try:
                if v.lower() == "true": final = True
                elif v.lower() == "false": final = False
                elif v.startswith("#"): final = v 
                else: final = float(v) if "." in v else int(v)
                if final != old_val: state_manager.update_state(final, path=full_path, source=source)
            except Exception as e:
                from oaLogging.Entry import logger
                matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"LeafEditorFactory: Silently ignoring conversion error for '{v}': {e}", "TRACE")

        entry.bind("<FocusIn>", focus_in)
        entry.bind("<FocusOut>", focus_out)
        entry.bind("<Return>", lambda e: source.focus_set())
