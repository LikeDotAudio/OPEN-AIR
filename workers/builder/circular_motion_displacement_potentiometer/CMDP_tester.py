import tkinter as tk
from tkinter import ttk, simpledialog, colorchooser
import math
import random

# --- CONSTANTS ---
NEAR_RADIUS = 120
FAR_RADIUS = 380
ACCENT_COLOR = "#f4902c" # Orange

GROUPS = [
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

class LTPObject:
    def __init__(self, canvas, widget_id, length, angle_deg, color, group_idx, label, on_change_cb):
        self.canvas = canvas
        self.widget_id = widget_id
        self.track_len = length
        self.angle = angle_deg
        self.color_highlight = color
        self.group_index = group_idx
        self.label = label
        self.on_change_cb = on_change_cb
        
        self.x, self.y = 0, 0 
        
        # State
        self.visible = True
        self.val_min, self.val_max = 0.0, 100.0
        self.val_current = 20 + (random.random() * 70)
        self.rot_min, self.rot_max = 0.0, 100.0
        self.rot_current = 70 + (random.random() * 20)
        
        # Style
        self.cap_color = "#333333"
        self.cap_outline_normal = "#888888"
        self.cap_outline_hover = ACCENT_COLOR
        self.tag_root = f"fader_{self.widget_id}"
        
        self.dragging = False
        self.hovered = False
        
        self.start_x, self.start_y = 0, 0
        self.start_val, self.start_rot = 0, 0
        
        self.update_position()
        self.render()

    def update_position(self):
        rad = math.radians(self.angle)
        dist = NEAR_RADIUS + (self.track_len / 2)
        cx, cy = 600, 450 
        self.x = cx + dist * math.cos(rad)
        self.y = cy + dist * math.sin(rad)

    def rotate_point(self, px, py, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        nx = cos_a * (px - cx) - sin_a * (py - cy) + cx
        ny = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return nx, ny

    def render(self):
        self.canvas.delete(self.tag_root)
        if not self.visible: return

        cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len
        t_ang = ang + 90
        
        # Hitbox 
        hb_w = 60
        hbp = [
            self.rotate_point(cx - hb_w/2, cy - tl/2 - 20, cx, cy, t_ang),
            self.rotate_point(cx + hb_w/2, cy - tl/2 - 20, cx, cy, t_ang),
            self.rotate_point(cx + hb_w/2, cy + tl/2 + 20, cx, cy, t_ang),
            self.rotate_point(cx - hb_w/2, cy + tl/2 + 20, cx, cy, t_ang)
        ]
        flat_hbp = [coord for pt in hbp for coord in pt]
        self.canvas.create_polygon(flat_hbp, fill="", outline="", tags=(self.tag_root, "hitbox"))

        # Track
        p1 = self.rotate_point(cx, cy - tl/2, cx, cy, t_ang)
        p2 = self.rotate_point(cx, cy + tl/2, cx, cy, t_ang)
        self.canvas.create_line(p1, p2, fill="#000000", width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(p1, p2, fill="#222222", width=2, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Ticks (Enhanced)
        for i in range(11):
            norm = i / 10.0
            # 0 = Top/Near (-tl/2), 1 = Bottom/Far (+tl/2)
            # Wait, render logic: rotate_point(cx, cy + local_y)
            # local_y = -tl/2 + norm*tl
            # If norm=0, local_y = -tl/2 (Top).
            # If norm=1, local_y = +tl/2 (Bottom).
            local_y = (-tl/2) + (norm * tl)
            
            leng = 10 if i % 5 == 0 else 5
            
            # Left Tick
            tp1_x, tp1_y = self.rotate_point(cx - 15, cy + local_y, cx, cy, t_ang)
            tp2_x, tp2_y = self.rotate_point(cx - 15 - leng, cy + local_y, cx, cy, t_ang)
            self.canvas.create_line(tp1_x, tp1_y, tp2_x, tp2_y, fill="#888888", width=2, tags=self.tag_root)
            
            # Right Tick
            tp3_x, tp3_y = self.rotate_point(cx + 15, cy + local_y, cx, cy, t_ang)
            tp4_x, tp4_y = self.rotate_point(cx + 15 + leng, cy + local_y, cx, cy, t_ang)
            self.canvas.create_line(tp3_x, tp3_y, tp4_x, tp4_y, fill="#888888", width=2, tags=self.tag_root)

        # Cap
        norm = (self.val_current - self.val_min) / (self.val_max - self.val_min)
        local_cap_y = (-tl/2) + (norm * tl)
        
        ccx, ccy = self.rotate_point(cx, cy + local_cap_y, cx, cy, t_ang)
        r = 22
        
        outline_col = self.cap_outline_hover if self.hovered else self.cap_outline_normal
        outline_width = 4 if self.hovered else 2
        fill_col = "#555555" if self.hovered else self.cap_color
        
        self.canvas.create_oval(ccx-r, ccy-r, ccx+r, ccy+r, fill=fill_col, outline=outline_col, width=outline_width, tags=(self.tag_root, "cap"))
        
        # Sweep
        current_deg = 225 - (self.rot_current / 100.0) * 270
        self.canvas.create_arc(ccx-r+5, ccy-r+5, ccx+r-5, ccy+r-5, start=225, extent=-(225-current_deg), 
                               style=tk.ARC, outline=self.color_highlight, width=4, tags=self.tag_root)
        
        # Pointer
        ptr_rad = math.radians(current_deg)
        px = ccx + (r-2) * math.cos(ptr_rad)
        py = ccy - (r-2) * math.sin(ptr_rad) 
        self.canvas.create_line(ccx, ccy, px, py, fill=self.color_highlight, width=3, tags=self.tag_root)
        
        # VOL (Inside, Lower)
        self.canvas.create_text(ccx, ccy + 12, text=str(int(self.rot_current)), fill=self.color_highlight, font=("Arial", 9, "bold"), tags=self.tag_root)
        
        # DIST (Outside, Upper)
        self.canvas.create_text(ccx, ccy - 32, text=str(int(self.val_current)), fill="#CCCCCC", font=("Arial", 8), tags=self.tag_root)
        
        # Label (Staggered or Center on Hover)
        is_active = self.dragging or self.hovered
        
        if is_active:
            # Center of head
            lx, ly = 600, 450
            font_spec = ("Arial", 12, "bold")
        else:
            stagger = (self.widget_id % 2) * 25
            lab_dist = FAR_RADIUS + 25 + stagger
            l_rad = math.radians(self.angle)
            lx = 600 + lab_dist * math.cos(l_rad)
            ly = 450 + lab_dist * math.sin(l_rad)
            font_spec = ("Arial", 10)
        
        self.canvas.create_text(lx, ly, text=self.label, fill=self.color_highlight, font=font_spec, tags=self.tag_root)

    def set_hover(self, state):
        if self.visible and self.hovered != state:
            self.hovered = state
            self.render()

    def lift(self):
        self.canvas.tag_raise(self.tag_root)

class MultiFaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CMPD - 48 Channel Array - Python Prototype")
        self.geometry("1400x900")
        self.configure(bg="#222222")
        
        sidebar = tk.Frame(self, bg="#333333", width=200)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        
        cols = ("ID", "Name", "Dist", "Vol", "Angle")
        self.tree = ttk.Treeview(sidebar, columns=cols, show="headings", height=20)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=40)
        self.tree.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        tk.Label(sidebar, text="GROUPS", bg="#333", fg=ACCENT_COLOR, font=("Arial", 10, "bold")).pack(pady=5)
        self.group_labels = []
        self.group_vars = []
        self.group_buttons = []
        
        for idx, grp in enumerate(GROUPS):
            f = tk.Frame(sidebar, bg="#333")
            f.pack(fill=tk.X, padx=2, pady=2)
            
            iv = tk.BooleanVar(value=True)
            self.group_vars.append(iv)
            
            # Visibility Button (Eye)
            btn_vis = tk.Button(f, text="👁", bg=ACCENT_COLOR, fg="black", width=3, bd=0, 
                                command=lambda i=idx: self.click_group_vis(i))
            btn_vis.pack(side=tk.LEFT, padx=2)
            btn_vis.bind("<Double-Button-1>", lambda e, i=idx: self.solo_group(i))
            self.group_buttons.append(btn_vis)
            
            lbl = tk.Label(f, text=grp["name"], bg="#333", fg=grp["color"], width=12, anchor="w", cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.group_labels.append(lbl)
            
            lbl.bind("<Button-2>", lambda e, i=idx: self.on_group_drag_start(e, i))
            lbl.bind("<B2-Motion>", self.on_group_drag_move)
            lbl.bind("<ButtonRelease-2>", self.on_group_drag_end)
            
            lbl.bind("<Button-1>", lambda e, i=idx: self.select_group(i))
            lbl.bind("<Double-Button-1>", lambda e, i=idx, l=lbl: self.rename_group(i, l))
            lbl.bind("<Button-3>", lambda e, i=idx: self.pick_group_color(i))

        self.canvas = tk.Canvas(self, bg="#222222", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.faders = []
        self.center_x, self.center_y = 600, 450
        
        fader_count = 0
        for g_idx, grp in enumerate(GROUPS):
            for k in range(grp["count"]):
                i = fader_count
                name = BAND_NAMES[i]
                color = grp["color"]
                angle = random.random() * 360
                track_len = FAR_RADIUS - NEAR_RADIUS
                
                f = LTPObject(self.canvas, i, track_len, angle, color, g_idx, name, self.update_table)
                self.faders.append(f)
                self.tree.insert("", "end", iid=str(i), values=(i+1, name, int(f.val_current), int(f.rot_current), int(f.angle)))
                fader_count += 1
        
        self.draw_static_ui()
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-2>", self.on_mid_click)
        self.canvas.bind("<B2-Motion>", self.on_mid_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_release)
        self.canvas.bind("<Button-3>",self.on_right_click)
        self.canvas.bind("<B3-Motion>", self.on_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-4>", self.on_scroll)
        self.canvas.bind("<Button-5>", self.on_scroll)
        self.canvas.bind("<Motion>", self.on_motion)
        
        self.active_fader = None
        self.hovered_fader = None
        self.group_drag_state = None
        self.selected_group = -1

    def draw_static_ui(self):
        cx, cy = self.center_x, self.center_y
        self.canvas.create_oval(cx-NEAR_RADIUS, cy-NEAR_RADIUS, cx+NEAR_RADIUS, cy+NEAR_RADIUS, outline=ACCENT_COLOR, dash=(5,5), width=2, tags="guide")
        self.canvas.create_oval(cx-FAR_RADIUS, cy-FAR_RADIUS, cx+FAR_RADIUS, cy+FAR_RADIUS, outline=ACCENT_COLOR, dash=(5,5), width=2, tags="guide")
        
        r = 40
        # Ears
        self.canvas.create_oval(cx-r-10, cy-15, cx-r+5, cy+15, fill="#444", outline=ACCENT_COLOR, width=2, tags="head")
        self.canvas.create_oval(cx+r-5, cy-15, cx+r+10, cy+15, fill="#444", outline=ACCENT_COLOR, width=2, tags="head")
        
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#444", outline=ACCENT_COLOR, width=2, tags="head")
        self.canvas.create_polygon(cx, cy-r-15, cx-10, cy-r+5, cx+10, cy-r+5, fill=ACCENT_COLOR, tags="head")

    def click_group_vis(self, g_idx):
        # Toggle boolean var
        current = self.group_vars[g_idx].get()
        self.group_vars[g_idx].set(not current)
        self.update_group_btn_style(g_idx)
        self.toggle_group(g_idx)

    def update_group_btn_style(self, g_idx):
        is_vis = self.group_vars[g_idx].get()
        btn = self.group_buttons[g_idx]
        if is_vis:
            btn.config(bg=ACCENT_COLOR, fg="black")
        else:
            btn.config(bg="#555", fg="#888")

    def pick_group_color(self, g_idx):
        curr_col = GROUPS[g_idx]["color"]
        color = colorchooser.askcolor(initialcolor=curr_col, title=f"Color: {GROUPS[g_idx]['name']}")
        if color[1]:
            new_col = color[1]
            GROUPS[g_idx]["color"] = new_col
            self.group_labels[g_idx].config(fg=new_col)
            # Update faders
            for f in self.faders:
                if f.group_index == g_idx:
                    f.color_highlight = new_col
                    f.render()

    def toggle_group(self, g_idx):
        visible = self.group_vars[g_idx].get()
        for f in self.faders:
            if f.group_index == g_idx:
                f.visible = visible
                f.render()

    def solo_group(self, g_idx):
        for i, var in enumerate(self.group_vars):
            is_target = (i == g_idx)
            var.set(is_target)
            self.update_group_btn_style(i)
            for f in self.faders:
                if f.group_index == i:
                    f.visible = is_target
                    f.render()

    def rename_group(self, g_idx, lbl):
        new_name = simpledialog.askstring("Rename", "New Group Name:", initialvalue=lbl.cget("text"))
        if new_name:
            lbl.config(text=new_name)
            GROUPS[g_idx]["name"] = new_name

    def select_group(self, g_idx):
        if self.selected_group == g_idx:
            self.selected_group = -1
        else:
            self.selected_group = g_idx
        
        # Reset all labels
        for idx, lbl in enumerate(self.group_labels):
            lbl.config(bg="#333", fg=GROUPS[idx]["color"])
            
        # Highlight selected
        if self.selected_group != -1:
            self.group_labels[self.selected_group].config(bg=ACCENT_COLOR, fg="black")
        
        # Filter Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        for f in self.faders:
            if self.selected_group == -1 or f.group_index == self.selected_group:
                self.tree.insert("", "end", iid=str(f.widget_id), values=(f.widget_id+1, f.label, int(f.val_current), int(f.rot_current), int(f.angle)))

    def on_group_drag_start(self, event, g_idx):
        self.group_drag_state = { "index": g_idx, "startX": event.x_root }

    def on_group_drag_move(self, event):
        if self.group_drag_state:
            dx = event.x_root - self.group_drag_state["startX"]
            rot = dx * 0.5
            for f in self.faders:
                if f.group_index == self.group_drag_state["index"]:
                    f.angle += rot
                    f.update_position()
                    f.render()
            self.group_drag_state["startX"] = event.x_root

    def on_group_drag_end(self, event):
        self.group_drag_state = None

    def get_fader_at(self, x, y):
        # Reverse check
        for f in reversed(self.faders):
            if not f.visible: continue
            
            # Hit Test Cap logic specific to Tkinter coords
            rad = math.radians(f.angle)
            dist = NEAR_RADIUS + (f.track_len/2)
            cx = self.center_x + dist*math.cos(rad)
            cy = self.center_y + dist*math.sin(rad)
            
            norm = (f.val_current - f.val_min) / (f.val_max - f.val_min)
            local_cap_y = (-f.track_len/2) + (norm * f.track_len)
            
            t_ang = f.angle + 90
            c_rad = math.radians(t_ang)
            
            ccx, ccy = f.rotate_point(cx, cy + local_cap_y, cx, cy, t_ang)
            
            # Increased threshold 40
            if math.hypot(x - ccx, y - ccy) < 40: return f
        return None

    def on_motion(self, event):
        f = self.get_fader_at(event.x, event.y)
        if f != self.hovered_fader:
            if self.hovered_fader: self.hovered_fader.set_hover(False)
            if f: f.set_hover(True)
            self.hovered_fader = f

    def on_click(self, event):
        f = self.get_fader_at(event.x, event.y)
        if f:
            self.active_fader = f
            f.dragging = True
            f.lift()
            f.start_val = f.val_current
            f.start_x, f.start_y = event.x, event.y

    def on_drag(self, event):
        f = self.active_fader
        if f and f.dragging:
            is_alt = (event.state & 0x0008) or (event.state & 0x20000)
            
            if is_alt:
                # Rotate Azimuth
                dx = event.x - self.center_x
                dy = event.y - self.center_y
                f.angle = math.degrees(math.atan2(dy, dx))
                f.update_position()
                f.render()
            else:
                # Linear
                dx = event.x - f.start_x
                dy = event.y - f.start_y
                
                rad = math.radians(f.angle)
                tx, ty = math.cos(rad), math.sin(rad)
                proj = dx*tx + dy*ty
                
                # Invert: Out = Decrease
                change = -(proj / f.track_len) * 100
                f.val_current = max(0, min(100, f.start_val + change))
                f.render()
            self.update_table(f.widget_id, f.val_current, f.rot_current, f.angle, 0, 0)

    def on_mid_click(self, event):
        f = self.get_fader_at(event.x, event.y)
        if f:
            self.active_fader = f
            f.dragging = True # Reuse drag flag but use mid logic

    def on_mid_drag(self, event):
        # Middle Drag on Fader -> Move Azimuth (Rotation)
        f = self.active_fader
        if f and f.dragging:
            dx = event.x - self.center_x
            dy = event.y - self.center_y
            f.angle = math.degrees(math.atan2(dy, dx))
            f.update_position()
            f.render()
            self.update_table(f.widget_id, f.val_current, f.rot_current, f.angle, 0, 0)

    def on_right_click(self, event):
        f = self.get_fader_at(event.x, event.y)
        if f:
            self.active_fader = f
            f.dragging = True
            f.start_rot = f.rot_current
            f.start_y = event.y

    def on_right_drag(self, event):
        # Right Drag on Fader -> Adjust Rotation (Knob)
        f = self.active_fader
        if f and f.dragging:
            dy = f.start_y - event.y # Drag Up to increase
            change = (dy / 200.0) * 100 
            f.rot_current = max(0, min(100, f.start_rot + change))
            f.render()
            self.update_table(f.widget_id, f.val_current, f.rot_current, f.angle, 0, 0)

    def on_release(self, event):
        if self.active_fader:
            self.active_fader.dragging = False
            self.active_fader = None

    def on_scroll(self, event):
        f = self.get_fader_at(event.x, event.y)
        if f:
            delta = 1 if (event.delta > 0 or event.num == 4) else -1
            if event.state & 4: # Control Key
                f.angle += delta * 3
                f.update_position()
            else:
                f.rot_current = max(0, min(100, f.rot_current + delta * 5))
            f.render()
            self.update_table(f.widget_id, f.val_current, f.rot_current, f.angle, 0, 0)

    def update_table(self, wid, val, rot, angle, x, y):
        if self.tree.exists(str(wid)):
            self.tree.item(str(wid), values=(wid+1, self.faders[wid].label, int(val), int(rot), int(angle)))

if __name__ == "__main__":
    app = MultiFaderApp()
    app.mainloop()