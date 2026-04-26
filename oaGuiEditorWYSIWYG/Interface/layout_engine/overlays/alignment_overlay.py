# oaGuiEditorWYSIWYG/Interface/layout_engine/overlays/alignment_overlay.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular Alignment (Sticky) toolset indicators.

import tkinter as tk

from ....Core.state import state_manager
from .base_overlay import BaseOverlay


class AlignmentOverlay(BaseOverlay):
    """Handles visual indicators for widget alignment (sticky)."""

    def __init__(self, workspace, widget, path, is_focused):
        super().__init__(workspace, widget, path, is_focused)
        self.alignment_handles = {}
        self._build_ui()

    def _build_ui(self):
        for d in ["L", "R", "C", "T", "B"]:
            lbl = self.create_element(tk.Label, text=d, bg="#666666", fg="white", font=("Arial", 5, "bold"), cursor="hand2")
            self.alignment_handles[d] = lbl
            lbl.bind("<Button-1>", lambda e, m=d: self._toggle_sticky(m))

    def _toggle_sticky(self, mode):
        full_path = f"{self.path}.layout.sticky"
        current = str(state_manager.get_value_at_path(full_path) or "").lower()

        new_sticky = current
        if mode == "L": new_sticky = new_sticky.replace("w", "") if "w" in new_sticky else new_sticky + "w"
        elif mode == "R": new_sticky = new_sticky.replace("e", "") if "e" in new_sticky else new_sticky + "e"
        elif mode == "T": new_sticky = new_sticky.replace("n", "") if "n" in new_sticky else new_sticky + "n"
        elif mode == "B": new_sticky = new_sticky.replace("s", "") if "s" in new_sticky else new_sticky + "s"
        elif mode == "C": new_sticky = ""

        new_sticky = "".join(sorted(list(set(new_sticky))))
        state_manager.update_state(new_sticky.upper(), path=full_path, source=self.workspace)

    def sync(self, x, y, w, h):
        if not self.workspace.show_alignment.get():
            self.hide()
            return

        value = (state_manager.get_value_at_path(f"{self.path}.layout.sticky") or "").lower()
        self.alignment_handles["L"].config(bg="#33A1FD" if "w" in value else "#666666")
        self.alignment_handles["R"].config(bg="#33A1FD" if "e" in value else "#666666")
        self.alignment_handles["T"].config(bg="#33A1FD" if "n" in value else "#666666")
        self.alignment_handles["B"].config(bg="#33A1FD" if "s" in value else "#666666")
        self.alignment_handles["C"].config(bg="#33A1FD" if not value else "#666666")

        self.alignment_handles["L"].place(x=x, y=y + h//2 - 5, width=10, height=10)
        self.alignment_handles["R"].place(x=x + w - 10, y=y + h//2 - 5, width=10, height=10)
        self.alignment_handles["C"].place(x=x + w//2 - 5, y=y + h//2 - 5, width=10, height=10)
        self.alignment_handles["T"].place(x=x + w//2 - 5, y=y, width=10, height=10)
        self.alignment_handles["B"].place(x=x + w//2 - 5, y=y + h - 10, width=10, height=10)
