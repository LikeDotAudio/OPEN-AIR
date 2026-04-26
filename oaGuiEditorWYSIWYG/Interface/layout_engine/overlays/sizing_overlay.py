# oaGuiEditorWYSIWYG/Interface/layout_engine/overlays/sizing_overlay.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular Sizing and Padding handles.

import tkinter as tk

from ....Core.state import state_manager
from .base_overlay import BaseOverlay


class SizingOverlay(BaseOverlay):
    """Handles resize and padding interactive handles."""

    def __init__(self, workspace, widget, path, is_focused):
        super().__init__(workspace, widget, path, is_focused)
        self.handles = []
        self._build_ui()

    def _build_ui(self):
        self.res_diag = self.create_element(tk.Label, text="⤡", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sizing")
        self.res_horiz = self.create_element(tk.Label, text="↔", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sb_h_double_arrow")
        self.res_vert = self.create_element(tk.Label, text="↕", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sb_v_double_arrow")
        self.pad_x = self.create_element(tk.Label, text="PX", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="sb_h_double_arrow")
        self.pad_y = self.create_element(tk.Label, text="PY", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="sb_v_double_arrow")
        self.breath = self.create_element(tk.Label, text="BR", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="fleur")

        self.handles = [self.res_diag, self.res_horiz, self.res_vert, self.pad_x, self.pad_y, self.breath]

        for m, h in [("diag", self.res_diag), ("horiz", self.res_horiz), ("vert", self.res_vert),
                    ("padx", self.pad_x), ("pady", self.pad_y), ("breath", self.breath)]:
            h.bind("<Button-1>", lambda e, mode=m: self._on_drag(e, mode))
            h.bind("<B1-Motion>", lambda e, mode=m: self._on_drag(e, mode))
            h.bind("<ButtonRelease-1>", lambda e, mode=m: self._on_release(e, mode))

    def _on_drag(self, event, mode):
        if not self.widget.winfo_exists(): return
        dx, dy = event.x_root - self.widget.winfo_rootx(), event.y_root - self.widget.winfo_rooty()

        # UI FEEDBACK (Tooltip + Ghost) - Managed by workspace
        if hasattr(self.workspace, '_show_sizing_feedback'):
            self.workspace._show_sizing_feedback(event, mode, dx, dy, self.widget)

    def _on_release(self, event, mode):
        if hasattr(self.workspace, '_clear_sizing_feedback'):
            self.workspace._clear_sizing_feedback()

        if not self.widget.winfo_exists(): return
        dx, dy = event.x_root - self.widget.winfo_rootx(), event.y_root - self.widget.winfo_rooty()

        if mode == "padx":
            state_manager.update_state(max(0, int(dx // 5)), path=f"{self.path}.layout.padx", source=self.workspace)
        elif mode == "pady":
            state_manager.update_state(max(0, int(dy // 5)), path=f"{self.path}.layout.pady", source=self.workspace)
        elif mode == "breath":
            state_manager.update_state(max(0, int(dx // 5)), path=f"{self.path}.layout.breath_padding", source=self.workspace)
        else:
            nw, nh = max(20, dx), max(20, dy)
            updates = []
            geo_prefix = "" if "_config" in self.path else ".geometry"
            if mode in ["diag", "horiz"]: updates.append((int(nw), f"{self.path}{geo_prefix}.width"))
            if mode in ["diag", "vert"]: updates.append((int(nh), f"{self.path}{geo_prefix}.height"))
            state_manager.batch_update(updates, source=self.workspace)

    def sync(self, x, y, w, h):
        if self.workspace.show_sizing.get() and w >= 40 and h >= 40:
            self.res_diag.place(x=x + w - 20, y=y + h - 20, width=20, height=20)
            self.res_horiz.place(x=x + w - 20, y=y + (h//2) - 10, width=20, height=20)
            self.res_vert.place(x=x + (w//2) - 10, y=y + h - 20, width=20, height=20)
            self.pad_x.place(x=x + w - 40, y=y, width=18, height=12)
            self.pad_y.place(x=x + w - 20, y=y, width=18, height=12)
            self.breath.place(x=x + w - 60, y=y, width=18, height=12)
        else:
            self.hide()
