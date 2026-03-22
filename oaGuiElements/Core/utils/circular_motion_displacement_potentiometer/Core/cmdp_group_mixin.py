# Core/cmdp_group_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import colorchooser, simpledialog

ACCENT_COLOR = "#f4902c"

class CMDPGroupMixin:
    """Handles visibility, soloing, coloring, and batch transformations for fader groups."""

    def click_group_vis(self, g_idx):
        var = self.group_vars[g_idx]
        var.set(not var.get())
        self.update_group_btn_style(g_idx)
        self._sync_group_visibility(g_idx)

    def update_group_btn_style(self, g_idx):
        is_vis = self.group_vars[g_idx].get()
        self.group_buttons[g_idx].config(bg=ACCENT_COLOR if is_vis else "#555", fg="black" if is_vis else "#888")

    def pick_group_color(self, g_idx):
        curr = self.groups[g_idx]["color"]
        color = colorchooser.askcolor(initialcolor=curr, title=f"Color: {self.groups[g_idx]['name']}")
        if color[1]:
            new_col = color[1]
            self.groups[g_idx]["color"] = new_col
            self.group_labels[g_idx].config(fg=new_col)
            for f in self.faders:
                if f.group_index == g_idx:
                    f.color_highlight = new_col; f.render()

    def solo_group(self, g_idx):
        for i, var in enumerate(self.group_vars):
            is_target = (i == g_idx); var.set(is_target); self.update_group_btn_style(i)
            self._sync_group_visibility(i)

    def rename_group(self, g_idx, lbl):
        new = simpledialog.askstring("Rename", "New Name:", initialvalue=lbl.cget("text"))
        if new: lbl.config(text=new); self.groups[g_idx]["name"] = new

    def select_group(self, g_idx):
        self.selected_group = -1 if self.selected_group == g_idx else g_idx
        for i, lbl in enumerate(self.group_labels):
            lbl.config(bg=ACCENT_COLOR if i == self.selected_group else "#333", 
                       fg="black" if i == self.selected_group else self.groups[i]["color"])
        self._refresh_table_view()

    def on_group_drag_start(self, event, g_idx):
        self.group_drag_state = { "index": g_idx, "startX": event.x_root }

    def on_group_drag_move(self, event):
        if self.group_drag_state:
            dx = event.x_root - self.group_drag_state["startX"]
            for f in self.faders:
                if f.group_index == self.group_drag_state["index"]:
                    f.angle += dx * 0.5; f.update_position(); f.render()
            self.group_drag_state["startX"] = event.x_root

    def _sync_group_visibility(self, g_idx):
        visible = self.group_vars[g_idx].get()
        for f in self.faders:
            if f.group_index == g_idx: f.visible = visible; f.render()

    def _refresh_table_view(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for f in self.faders:
            if self.selected_group == -1 or f.group_index == self.selected_group:
                self.tree.insert("", "end", iid=str(f.widget_id), 
                                 values=(f.widget_id+1, f.label, int(f.val_current), int(f.rot_current), int(f.angle)))
