import tkinter as tk
from tkinter import ttk
import math

# --- UNBOUNDED FLOATING LTP (SINGLE CANVAS ARCHITECTURE) ---

class LTPObject:
    def __init__(self, canvas, widget_id, x, y, on_change_cb):
        self.canvas = canvas
        self.widget_id = widget_id
        self.x = x
        self.y = y
        self.angle = 0.0
        
        # State
        self.val_min, self.val_max, self.val_current = 0.0, 100.0, 50.0
        self.rot_min, self.rot_max, self.rot_current = -130.0, 130.0, 0.0
        
        # Style
        self.cap_color = "#333333"
        self.cap_outline_normal = "#888888"
        self.cap_outline_hover = "#00ffff" # Cyan glow
        self.cap_outline = self.cap_outline_normal
        self.highlight_color = "#00bfff"
        self.track_len = 200
        
        self.on_change_cb = on_change_cb
        self.tag_root = f"fader_{self.widget_id}"
        
        self.dragging = False
        self.hovered = False
        
        self.start_x, self.start_y = 0, 0
        self.start_val, self.start_rot = 0, 0
        self.start_pos = (0, 0)
        
        self.render()

    def rotate_point(self, px, py, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        nx = cos_a * (px - cx) - sin_a * (py - cy) + cx
        ny = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return nx, ny

    def render(self):
        self.canvas.delete(self.tag_root)
        cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len
        
        # Hitbox
        hb_w = 60
        hbp = [
            self.rotate_point(cx - hb_w/2, cy - tl/2 - 20, cx, cy, ang),
            self.rotate_point(cx + hb_w/2, cy - tl/2 - 20, cx, cy, ang),
            self.rotate_point(cx + hb_w/2, cy + tl/2 + 20, cx, cy, ang),
            self.rotate_point(cx - hb_w/2, cy + tl/2 + 20, cx, cy, ang)
        ]
        flat_hbp = [coord for pt in hbp for coord in pt]
        self.canvas.create_polygon(flat_hbp, fill="", outline="", tags=(self.tag_root, "hitbox"))

        # Track
        p1 = self.rotate_point(cx, cy - tl/2, cx, cy, ang)
        p2 = self.rotate_point(cx, cy + tl/2, cx, cy, ang)
        self.canvas.create_line(p1, p2, fill="#000000", width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(p1, p2, fill="#222222", width=2, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Ticks
        for i in range(11):
            ly = (cy + tl/2) - (tl * (i/10))
            leng = 10 if i % 5 == 0 else 5
            tp1, tp2 = self.rotate_point(cx-15, ly, cx, cy, ang), self.rotate_point(cx-15-leng, ly, cx, cy, ang)
            self.canvas.create_line(tp1, tp2, fill="#666666", tags=self.tag_root)
            tp3, tp4 = self.rotate_point(cx+15, ly, cx, cy, ang), self.rotate_point(cx+15+leng, ly, cx, cy, ang)
            self.canvas.create_line(tp3, tp4, fill="#666666", tags=self.tag_root)

        # Cap
        norm = (self.val_current - self.val_min) / (self.val_max - self.val_min)
        local_cap_y = (cy + tl/2) - (norm * tl)
        ccx, ccy = self.rotate_point(cx, local_cap_y, cx, cy, ang)
        r = 22
        
        # Glow Effect
        outline_col = self.cap_outline_hover if self.hovered else self.cap_outline_normal
        outline_w = 3 if self.hovered else 2
        
        self.canvas.create_oval(ccx-r, ccy-r, ccx+r, ccy+r, fill=self.cap_color, outline=outline_col, width=outline_w, tags=(self.tag_root, "cap"))
        
        prad = math.radians(90 - self.rot_current - ang)
        px, py = ccx + (r-2)*math.cos(prad), ccy - (r-2)*math.sin(prad)
        self.canvas.create_line(ccx, ccy, px, py, fill=self.highlight_color, width=3, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_oval(ccx-3, ccy-3, ccx+3, ccy+3, fill=self.highlight_color, outline="", tags=self.tag_root)
        
        self.canvas.create_text(ccx, ccy-35, text=f"{self.val_current:.1f}", fill="white", font=("Arial", 8), tags=self.tag_root)
        self.canvas.create_text(ccx, ccy+35, text=f"R:{self.rot_current:.0f}", fill="#aaaaaa", font=("Arial", 7), tags=self.tag_root)
        self.canvas.create_text(cx, cy + tl/2 + 30, text=f"ID:{self.widget_id}", fill="#555555", font=("Arial", 8), tags=self.tag_root)

    def set_hover(self, state):
        if self.hovered != state:
            self.hovered = state
            self.render()

    def lift(self):
        self.canvas.tag_raise(self.tag_root)

class MultiFaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Floating Transparent Faders (8 Units)")
        self.geometry("1200x900")
        self.configure(bg="#222222")
        
        ctrl_frame = tk.Frame(self, bg="#333333", padx=10, pady=10)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(ctrl_frame, text="Controls:\nMiddle-Drag = Move Widget | Alt+Scroll = Rotate Widget\nScroll (Hover) = Adjust Knob\nDrag Cap (Dual-Axis): Up/Down=Linear, Left/Right=Rotary", 
                 bg="#333333", fg="#eeeeee", justify="left").pack(side=tk.LEFT)
        
        cols = ("ID", "Linear", "Rotary", "Angle", "X", "Y")
        self.tree = ttk.Treeview(ctrl_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        self.tree.pack(side=tk.RIGHT, padx=20)
        
        self.canvas = tk.Canvas(self, bg="#444444", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.faders = []
        rows, cols = 2, 4
        start_x, start_y, gap_x, gap_y = 150, 200, 250, 300
        for i in range(8):
            r, c = i // cols, i % cols
            x, y = start_x + c * gap_x, start_y + r * gap_y
            fader = LTPObject(self.canvas, i, x, y, self.update_table)
            self.faders.append(fader)
            self.tree.insert("", "end", iid=str(i), values=(i, "50.0", "0", "0.0", x, y))

        # Bindings
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.canvas.bind("<Button-2>", self.on_mid_click)
        self.canvas.bind("<B2-Motion>", self.on_mid_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_release)
        
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Button-4>", self.on_scroll)
        self.canvas.bind("<Button-5>", self.on_scroll)
        
        self.canvas.bind("<Motion>", self.on_motion) # Hover detection
        
        self.active_fader = None
        self.hovered_fader = None

    def get_fader_at(self, x, y):
        item_id = self.canvas.find_closest(x, y, halo=5)
        if not item_id: return None
        tags = self.canvas.gettags(item_id[0])
        for tag in tags:
            if tag.startswith("fader_"):
                try:
                    return self.faders[int(tag.split("_")[1])]
                except:
                    pass
        return None

    def on_motion(self, event):
        fader = self.get_fader_at(event.x, event.y)
        if fader != self.hovered_fader:
            if self.hovered_fader: self.hovered_fader.set_hover(False)
            if fader: fader.set_hover(True)
            self.hovered_fader = fader

    def on_click(self, event):
        fader = self.get_fader_at(event.x, event.y)
        if fader:
            self.active_fader = fader
            fader.lift()
            fader.dragging = True
            fader.start_x, fader.start_y = event.x, event.y
            fader.start_val, fader.start_rot = fader.val_current, fader.rot_current

    def on_drag(self, event):
        fader = self.active_fader
        if fader and fader.dragging:
            dx, dy = event.x - fader.start_x, event.y - fader.start_y
            rad = math.radians(fader.angle)
            ldx = dx * math.cos(-rad) - dy * math.sin(-rad)
            ldy = dx * math.sin(-rad) + dy * math.cos(-rad)
            
            # Dual-Axis Control
            # Vertical (ldy) -> Linear
            # Horizontal (ldx) -> Rotary
            
            # Linear
            dv = -(ldy / fader.track_len) * (fader.val_max - fader.val_min)
            fader.val_current = max(fader.val_min, min(fader.val_max, fader.start_val + dv))
            
            # Rotary (Sensitivity: 1 pixel = 1 degree roughly? Scale it)
            rot_sens = 1.0
            fader.rot_current = max(fader.rot_min, min(fader.rot_max, fader.start_rot + (ldx * rot_sens)))
            
            fader.render()
            self.update_table(fader.widget_id, fader.val_current, fader.rot_current, fader.angle, fader.x, fader.y)

    def on_mid_click(self, event):
        fader = self.get_fader_at(event.x, event.y)
        if fader:
            self.active_fader = fader
            fader.lift()
            fader.dragging = True
            fader.start_x, fader.start_y = event.x, event.y
            fader.start_pos = (fader.x, fader.y)

    def on_mid_drag(self, event):
        fader = self.active_fader
        if fader and fader.dragging:
            dx, dy = event.x - fader.start_x, event.y - fader.start_y
            fader.x, fader.y = fader.start_pos[0] + dx, fader.start_pos[1] + dy
            fader.render()
            self.update_table(fader.widget_id, fader.val_current, fader.rot_current, fader.angle, fader.x, fader.y)

    def on_release(self, event):
        if self.active_fader:
            self.active_fader.dragging = False
            self.active_fader = None

    def on_scroll(self, event):
        fader = self.get_fader_at(event.x, event.y)
        if fader:
            delta = 0
            if event.num == 4: delta = 1
            elif event.num == 5: delta = -1
            elif hasattr(event, "delta"): delta = 1 if event.delta > 0 else -1
            
            if event.state & 0x0008: # Alt + Scroll -> Rotate Widget
                fader.angle += delta * 3
                fader.render()
            else: # Knob Value
                fader.rot_current = max(fader.rot_min, min(fader.rot_max, fader.rot_current + delta * 3))
                fader.render()
            self.update_table(fader.widget_id, fader.val_current, fader.rot_current, fader.angle, fader.x, fader.y)

    def update_table(self, wid, val, rot, angle, x, y):
        self.tree.item(str(wid), values=(wid, f"{val:.1f}", f"{rot:.1f}", f"{angle:.1f}", int(x), int(y)))

if __name__ == "__main__":
    app = MultiFaderApp()
    app.mainloop()