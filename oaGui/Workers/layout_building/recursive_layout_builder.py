# oaGui/Workers/layout_building/recursive_layout_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Builder for recursive/nested container GUI layouts.

import pathlib
import tkinter as tk

from .base_layout_builder import BaseLayoutBuilder


class RecursiveLayoutBuilder(BaseLayoutBuilder):
    """Constructs recursive/nested container layouts."""

    def build(self, path, parent_widget, layout_data, on_complete=None):
        container = tk.Frame(parent_widget, bg=self.scanner.theme_colors["bg"])
        container.pack(fill=tk.BOTH, expand=True)
        all_items = layout_data.get("gui_files", []) + layout_data.get("child_containers", [])

        if not all_items:
            if on_complete: on_complete()
            return

        container.grid_columnconfigure(0, weight=1)
        slots = []
        for i in range(len(all_items)):
            container.grid_rowconfigure(i, weight=1, uniform="group")
            slot = tk.Frame(container, bg=self.scanner.theme_colors["bg"])
            slot.grid(row=i, column=0, sticky="nsew")
            slots.append(slot)

        def _process_recursive(idx=0):
            if idx >= len(all_items):
                if on_complete: on_complete()
                return

            item = all_items[idx]
            slot = slots[idx]
            if isinstance(item, dict):
                self.scanner._build_from_directory(path=path, parent_widget=slot,
                                           on_complete=lambda: self.scanner.after(1, lambda: _process_recursive(idx + 1)),
                                           layout_override=item)
            elif isinstance(item, (str, pathlib.Path)):
                instance = self.scanner.loader_facade.load_and_instantiate_gui(path=item, parent_widget=slot)
                self.scanner._add_instance_to_parent(slot, instance, 0)
                self.scanner.after(1, lambda: _process_recursive(idx + 1))
            else:
                self.scanner.after(1, lambda: _process_recursive(idx + 1))

        _process_recursive(0)
