# circular_motion_displacement_potentiometer/CMDP_tester.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized CMPD Tester Application.

import tkinter as tk
from tkinter import ttk
import random

# --- EXTRACTED CORE MODULES ---
from core.cmdp_math import CircularMath
from core.ltp_fader import LTPFader, NEAR_RADIUS, FAR_RADIUS, ACCENT_COLOR
from core.cmdp_interaction_mixin import CMDPInteractionMixin
from core.cmdp_group_mixin import CMDPGroupMixin

GROUPS_DATA = [
    { "name": "Drums", "color": "#FF4444", "count": 12 },
    { "name": "Bass", "color": "#FFFF44", "count": 6 },
    { "name": "Guitars", "color": "#44FF44", "count": 6 },
    { "name": "Keys", "color": "#44FFFF", "count": 6 },
    { "name": "Vocals", "color": "#4444FF", "count": 6 },
    { "name": "Strings", "color": "#FF44FF", "count": 4 },
    { "name": "Brass", "color": "#FF4488", "count": 4 },
    { "name": "FX", "color": "#888888", "count": 4 }
]

BAND_NAMES = [
    "Kick In", "Kick Out", "Snare T", "Snare B", "Hat", "Ride", "Tom 1", "Tom 2", "Tom 3", "Floor 1", "Floor 2", "Gong",
    "Bass DI", "Bass Mic", "Bass Syn", "Upright", "Sub", "Bass FX",
    "Gtr 1 L", "Gtr 1 R", "Gtr 2 L", "Gtr 2 R", "Ac Gtr", "12 Str",
    "Piano L", "Piano R", "Organ L", "Organ R", "Synth 1", "Synth 2",
    "Lead Vox", "Double", "BGV 1", "BGV 2", "BGV 3", "BGV 4",
    "Violin 1", "Violin 2", "Viola", "Cello",
    "Trumpet", "Sax", "Trombone", "Tuba",
    "Rev 1", "Rev 2", "Delay", "Echo"
]

class MultiFaderApp(tk.Tk, CMDPInteractionMixin, CMDPGroupMixin):
    def __init__(self):
        super().__init__()
        self.title("CMPD - 48 Channel Array - Python Prototype")
        self.geometry("1400x900"); self.configure(bg="#222222")
        
        self.groups = GROUPS_DATA
        self.center_x, self.center_y = 600, 450
        self.active_fader = None; self.hovered_fader = None
        self.selected_group = -1; self.group_drag_state = None
        
        self._setup_sidebar()
        self._setup_canvas()
        self._initialize_faders()
        self._draw_static_ui()

    def _setup_sidebar(self):
        sidebar = tk.Frame(self, bg="#333333", width=200); sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 1. Group List
        tk.Label(sidebar, text="GROUPS", bg="#333", fg=ACCENT_COLOR, font=("Arial", 10, "bold")).pack(pady=5)
        self.group_labels, self.group_vars, self.group_buttons = [], [], []
        for idx, grp in enumerate(self.groups):
            f = tk.Frame(sidebar, bg="#333"); f.pack(fill=tk.X, padx=2, pady=2)
            iv = tk.BooleanVar(value=True); self.group_vars.append(iv)
            
            btn = tk.Button(f, text="👁", bg=ACCENT_COLOR, width=3, bd=0, command=lambda i=idx: self.click_group_vis(i))
            btn.pack(side=tk.LEFT, padx=2); btn.bind("<Double-1>", lambda e, i=idx: self.solo_group(i))
            self.group_buttons.append(btn)
            
            lbl = tk.Label(f, text=grp["name"], bg="#333", fg=grp["color"], width=12, anchor="w", cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True); self.group_labels.append(lbl)
            
            lbl.bind("<Button-2>", lambda e, i=idx: self.on_group_drag_start(e, i))
            lbl.bind("<B2-Motion>", self.on_group_drag_move)
            lbl.bind("<ButtonRelease-2>", lambda e: setattr(self, 'group_drag_state', None))
            lbl.bind("<Button-1>", lambda e, i=idx: self.select_group(i))
            lbl.bind("<Double-1>", lambda e, i=idx, l=lbl: self.rename_group(i, l))
            lbl.bind("<Button-3>", lambda e, i=idx: self.pick_group_color(i))

        # 2. Table
        cols = ("ID", "Name", "Dist", "Vol", "Angle")
        self.tree = ttk.Treeview(sidebar, columns=cols, show="headings", height=20)
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=40)
        self.tree.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def _setup_canvas(self):
        self.canvas = tk.Canvas(self, bg="#222222", highlightthickness=0); self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click); self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release); self.canvas.bind("<Button-2>", self.on_mid_click)
        self.canvas.bind("<B2-Motion>", self.on_mid_drag); self.canvas.bind("<ButtonRelease-2>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click); self.canvas.bind("<B3-Motion>", self.on_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_release); self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-4>", self.on_scroll); self.canvas.bind("<Button-5>", self.on_scroll)
        self.canvas.bind("<Motion>", self.on_motion)

    def _initialize_faders(self):
        self.faders = []; count = 0
        for g_idx, grp in enumerate(self.groups):
            for _ in range(grp["count"]):
                f = LTPFader(self.canvas, count, FAR_RADIUS - NEAR_RADIUS, random.random()*360, grp["color"], g_idx, BAND_NAMES[count])
                self.faders.append(f)
                self.tree.insert("", "end", iid=str(count), values=(count+1, f.label, int(f.val_current), int(f.rot_current), int(f.angle)))
                count += 1

    def _draw_static_ui(self):
        cx, cy = self.center_x, self.center_y
        self.canvas.create_oval(cx-NEAR_RADIUS, cy-NEAR_RADIUS, cx+NEAR_RADIUS, cy+NEAR_RADIUS, outline=ACCENT_COLOR, dash=(5,5), width=2, tags="guide")
        self.canvas.create_oval(cx-FAR_RADIUS, cy-FAR_RADIUS, cx+FAR_RADIUS, cy+FAR_RADIUS, outline=ACCENT_COLOR, dash=(5,5), width=2, tags="guide")
        r = 40
        self.canvas.create_oval(cx-r-10, cy-15, cx-r+5, cy+15, fill="#444", outline=ACCENT_COLOR, width=2, tags="head")
        self.canvas.create_oval(cx+r-5, cy-15, cx+r+10, cy+15, fill="#444", outline=ACCENT_COLOR, width=2, tags="head")
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#444", outline=ACCENT_COLOR, width=2, tags="head")
        self.canvas.create_polygon(cx, cy-r-15, cx-10, cy-r+5, cx+10, cy-r+5, fill=ACCENT_COLOR, tags="head")

    def update_table(self, wid, val, rot, angle):
        if self.tree.exists(str(wid)):
            self.tree.item(str(wid), values=(wid+1, self.faders[wid].label, int(val), int(rot), int(angle)))

if __name__ == "__main__":
    MultiFaderApp().mainloop()