# oaGui/Workers/layout_building/multi_window_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Builder for multi-window GUI layouts.

import tkinter as tk

from .base_layout_builder import BaseLayoutBuilder


class MultiWindowBuilder(BaseLayoutBuilder):
    """Orchestrates multi-window instantiation."""

    def build(self, path, parent_widget, layout_data, on_complete=None):
        windows = layout_data.get("windows", [])

        def _process_windows(win_idx=0):
            if win_idx >= len(windows):
                if on_complete: on_complete()
                return

            win_data = windows[win_idx]
            path_to_build = win_data["path"]
            title = win_data["title"]

            if win_idx == 0:
                target_widget = parent_widget
                root = getattr(self.scanner, "root", None)
                if root and isinstance(root, tk.Tk):
                    root.title(f"OPEN-AIR: {title}")
            else:
                root = getattr(self.scanner, "root", None)
                target_window = tk.Toplevel(root) if root and isinstance(root, tk.Tk) else tk.Toplevel()
                target_window.title(f"OPEN-AIR: {title}")
                target_window.geometry("1024x768")
                target_window.configure(bg=self.scanner.theme_colors["bg"])
                target_widget = tk.Frame(target_window, bg=self.scanner.theme_colors["bg"])
                target_widget.pack(fill=tk.BOTH, expand=True)

            self.scanner._build_from_directory(
                path=path_to_build,
                parent_widget=target_widget,
                on_complete=lambda: self.scanner.after(1, lambda: _process_windows(win_idx + 1))
            )

        self.scanner.after(1, lambda: _process_windows(0))
