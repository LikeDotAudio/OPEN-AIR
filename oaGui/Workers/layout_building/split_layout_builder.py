# oaGui/Workers/layout_building/split_layout_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Builder for split-pane (horizontal/vertical) GUI layouts.

import tkinter as tk
from tkinter import ttk

from oaLogging.Methods.matrix_gate import matrix_log

from .base_layout_builder import BaseLayoutBuilder


class SplitLayoutBuilder(BaseLayoutBuilder):
    """Constructs split-pane (horizontal/vertical) layouts."""

    def build(self, path, parent_widget, layout_data, on_complete=None):
        orientation = layout_data.get("orientation", tk.HORIZONTAL)
        paned_window = ttk.PanedWindow(parent_widget, orient=orientation)
        matrix_log("gui", "gui_builder", "_build_split_layout", f"📐 [SPLIT] Creating {'Horizontal' if orientation == tk.HORIZONTAL else 'Vertical'} Split for {path}", "DEBUG")

        try:
            paned_window.pack(fill=tk.BOTH, expand=True)
        except tk.TclError as e:
            matrix_log("gui", "gui_builder", "_build_split_layout", f"⚠️ PanedWindow pack skipped: {e}", "TRACE")

        panels = layout_data.get("panels", [])
        matrix_log("gui", "gui_builder", "_build_split_layout", f"📐 [SPLIT] Found {len(panels)} panels for {path}", "DEBUG")
        overflow_ew = layout_data.get("overflow_ew", "none")
        overflow_ns = layout_data.get("overflow_ns", "none")

        containers = []
        for i, panel_data in enumerate(panels):
            p_path = panel_data.get("path")
            matrix_log("gui", "gui_builder", "_build_split_layout", f"📐 [SPLIT] Creating container for panel {i}: {p_path}", "DEBUG")
            base_frame = tk.Frame(paned_window, borderwidth=0, relief="flat", bg=self.scanner.theme_colors["bg"], width=1, height=1)
            base_frame.grid_rowconfigure(0, weight=1); base_frame.grid_columnconfigure(0, weight=1)

            target = base_frame
            if overflow_ew == "auto" or overflow_ns == "auto":
                from oaGui.Interface.controls.auto_scrollbar import AutoScrollbar
                canvas = tk.Canvas(base_frame, borderwidth=0, highlightthickness=0, relief="flat", bg=self.scanner.theme_colors["bg"])
                if overflow_ew == "auto":
                    h_scroll = AutoScrollbar(base_frame, orient=tk.HORIZONTAL, command=canvas.xview)
                    canvas.configure(xscrollcommand=h_scroll.set)
                    h_scroll.grid(row=1, column=0, sticky="ew")
                if overflow_ns == "auto":
                    v_scroll = AutoScrollbar(base_frame, orient=tk.VERTICAL, command=canvas.yview)
                    canvas.configure(yscrollcommand=v_scroll.set)
                    v_scroll.grid(row=0, column=1, sticky="ns")
                canvas.grid(row=0, column=0, sticky="nsew")
                target = canvas

            containers.append(target)
            paned_window.add(base_frame)
            paned_window.pane(base_frame, weight=int(panel_data.get("weight", 1)))

        def _process_panels(idx=0):
            if idx >= len(panels):
                if on_complete: on_complete()
                return

            override = {"behavior": {"overflow_ew": overflow_ew, "overflow_ns": overflow_ns}}
            self.scanner._build_from_directory(path=panels[idx]["path"], parent_widget=containers[idx],
                                       on_complete=lambda: _process_panels(idx + 1),
                                       layout_override=override)

        self.scanner.after(1, lambda: _process_panels(0))
        self._bind_sash_configuration(paned_window, panels, orientation)

    def _bind_sash_configuration(self, paned_window, panels, orientation):
        """Handles responsive sash positioning for PanedWindows."""
        paned_window.sash_config_in_progress = False

        def configure_sash(event=None):
            if not paned_window.winfo_exists() or getattr(paned_window, "sash_config_in_progress", False): return
            paned_window.sash_config_in_progress = True
            try:
                w, h = paned_window.winfo_width(), paned_window.winfo_height()
                if w <= 20 or h <= 20: return
                total_weight = sum(max(1, p.get("weight", 1)) for p in panels)
                if total_weight == 0: return
                size, cumulative = (w, 0) if orientation == tk.HORIZONTAL else (h, 0)
                last_pos = 0
                for i in range(len(panels) - 1):
                    cumulative += (size * max(1, panels[i].get("weight", 1))) / total_weight
                    pos = max(last_pos + 1, min(int(size) - (len(panels) - i), int(cumulative)))
                    paned_window.sashpos(i, max(1, int(pos)))
                    last_pos = pos
            except tk.TclError: pass
            finally: paned_window.sash_config_in_progress = False

        paned_window.bind("<Configure>", configure_sash, add="+")
        self.scanner.after(50, configure_sash)
