# Core/cmdp_tree.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk

class CMDPTreeManager:
    """Manages the channel tree pop-up window and its associated interactions."""

    def __init__(self, widget):
        self.w = widget

    def toggle(self):
        is_vis = not self.w.show_channels_var.get(); self.w.show_channels_var.set(is_vis)
        if is_vis:
            self.w.tree_window = tk.Toplevel(self.w); self.w.tree_window.title("Channel Tree"); self.w.tree_window.geometry("600x700")
            self.w.tree_window.protocol("WM_DELETE_WINDOW", self.toggle)
            
            s = ttk.Style(self.w.tree_window); s.configure("CMDP_Pop.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b")
            cols = ("Name", "Mute", "Level", "Depth", "Angle", "ID")
            self.w.pop_tree = ttk.Treeview(self.w.tree_window, columns=cols, show="tree headings", style="CMDP_Pop.Treeview")
            self.w.pop_tree.heading("#0", text="Groups")
            for c in cols: self.w.pop_tree.heading(c, text=c); self.w.pop_tree.column(c, width=70, anchor="center")
            self.w.pop_tree.pack(fill=tk.BOTH, expand=True)
            
            self.refresh()
            self.w.pop_tree.bind("<Button-1>", self._on_click)
            self.w.pop_tree.bind("<B1-Motion>", self._on_drag)
            self.w.pop_tree.bind("<ButtonRelease-1>", self._on_release)
            self.w.btn_toggle_channels.config(text="Channels ON", bg="#f4902c", fg="black")
        else:
            if self.w.tree_window: self.w.tree_window.destroy(); self.w.tree_window = self.w.pop_tree = None
            self.w.btn_toggle_channels.config(text="Channels OFF", bg="#444", fg="white")

    def refresh(self):
        if not self.w.pop_tree: return
        self.w.pop_tree.delete(*self.w.pop_tree.get_children())
        for gn in self.w.group_name_vars:
            m = "☐ Muted" if all(f.mute_var.get() for f in self.w.faders if f.group_name == gn) else "☑ Active"
            self.w.pop_tree.insert("", "end", iid=f"grp_{gn}", text=gn, values=("(Group)", m, "", "", "", ""), open=True)
        for i, f in enumerate(self.w.faders):
            p = f"grp_{f.group_name}" if f"grp_{f.group_name}" in self.w.pop_tree.get_children("") else ""
            m = "☐ Muted" if f.mute_var.get() else "☑ Active"
            self.w.pop_tree.insert(p, "end", iid=f"ch_{i}", text="", values=(f.label, m, int(float(f.rot_var.get())), int(float(f.val_var.get())), int(float(f.angle_var.get())), i+1))

    def _on_click(self, e):
        it = self.w.pop_tree.identify_row(e.y); col = self.w.pop_tree.identify_column(e.x)
        if not it: return
        if col == "#2":
            if it.startswith("ch_"): f = self.w.faders[int(it[3:])]; f.mute_var.set(not f.mute_var.get())
            elif it.startswith("grp_"): self.w.gh.toggle_group_mute(it[4:])
            self.refresh(); return
        if it.startswith("ch_") and col in ("#3", "#4", "#5"): self._spawn_edit(it, col, e); return
        if it.startswith("ch_"): self._drag_item = it
        else: self._drag_item = None

    def _spawn_edit(self, item, col, event):
        x, y, w, h = self.w.pop_tree.bbox(item, col); ch_idx = int(item[3:]); f = self.w.faders[ch_idx]
        var = f.rot_var if col == "#3" else f.val_var if col == "#4" else f.angle_var
        ent = tk.Entry(self.w.pop_tree, bg="white", fg="black", justify="center")
        ent.insert(0, str(int(float(var.get())))); ent.place(x=x, y=y, width=w, height=h); ent.focus_set(); ent.select_range(0, tk.END)
        def _save(e=None):
            try:
                var.set(float(ent.get()))
                if self.w.mixin_ref.state_mirror_engine:
                    p = "rot" if col == "#3" else "val" if col == "#4" else "angle"
                    self.w.mixin_ref.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.w.path}/ch{ch_idx}/{p}")
                self.refresh()
            except: pass
            ent.destroy()
        ent.bind("<Return>", _save); ent.bind("<FocusOut>", _save); ent.bind("<Escape>", lambda e: ent.destroy())

    def _on_drag(self, e):
        if getattr(self, "_drag_item", None): self.w.pop_tree.configure(cursor="hand2")

    def _on_release(self, e):
        if getattr(self, "_drag_item", None):
            tgt = self.w.pop_tree.identify_row(e.y)
            if tgt and tgt.startswith("grp_"):
                gn = tgt[4:]; ch_idx = int(self._drag_item[3:]); f = self.w.faders[ch_idx]
                f.group_name = gn; f.color_highlight = self.w.group_color_vars[gn].get(); self.refresh(); f.render()
            self.w.pop_tree.configure(cursor=""); self._drag_item = None