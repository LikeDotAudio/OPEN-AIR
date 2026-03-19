import tkinter as tk
from tkinter import ttk
import math

# --- UNBOUNDED FLOATING LTP (SINGLE CANVAS ARCHITECTURE) ---

# --- Constants ---
PERCENT_MAX = 100.0
ROTATION_MIN_DEFAULT = -130.0
ROTATION_MAX_DEFAULT = 130.0
DEFAULT_TRACK_LENGTH = 200
HITBOX_WIDTH = 60
HITBOX_PADDING = 20
TICK_COUNT = 11
TICK_DIVISOR = 10.0
TICK_MAJOR_INTERVAL = 5
TICK_MAJOR_LENGTH = 10
TICK_MINOR_LENGTH = 5
TICK_OFFSET = 15
CAP_RADIUS = 22
POINTER_OFFSET = 2
INDICATOR_OFFSET = 35
ID_LABEL_OFFSET = 30

class LTPObject:
    def __init__(self, canvas, widget_id, x, y, on_change_cb):
        self.canvas = canvas
        self.widget_id = widget_id
        self.x = x
        self.y = y
        self.angle = 0.0
        
        # State
        self.val_min, self.val_max, self.val_current = 0.0, PERCENT_MAX, 50.0
        self.rot_min, self.rot_max, self.rot_current = ROTATION_MIN_DEFAULT, ROTATION_MAX_DEFAULT, 0.0
        
        # Style
        self.cap_color = "#333333"
        self.cap_outline_normal = "#888888"
        self.cap_outline_hover = "#00ffff" # Cyan glow
        self.cap_outline = self.cap_outline_normal
        self.highlight_color = "#00bfff"
        self.track_len = DEFAULT_TRACK_LENGTH
        
        self.on_change_cb = on_change_cb
        self.tag_root = f"fader_{self.widget_id}"
        
        self.dragging = False
        self.hovered = False
        
        self.start_x, self.start_y = 0, 0
        self.start_val, self.start_rot = 0, 0
        self.start_pos = (0, 0)
        
        self.render_visuals()

    def calculate_rotated_point(self, px, py, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        new_x = cos_a * (px - cx) - sin_a * (py - cy) + cx
        new_y = sin_a * (px - cx) + cos_a * (py - cy) + cy
        return new_x, new_y

    def render_visuals(self):
        self.canvas.delete(self.tag_root)
        center_x, center_y, angle, track_length = self.x, self.y, self.angle, self.track_len
        
        # Hitbox
        hitbox_width = HITBOX_WIDTH
        hitbox_points = [
            self.calculate_rotated_point(center_x - hitbox_width/2, center_y - track_length/2 - HITBOX_PADDING, center_x, center_y, angle),
            self.calculate_rotated_point(center_x + hitbox_width/2, center_y - track_length/2 - HITBOX_PADDING, center_x, center_y, angle),
            self.calculate_rotated_point(center_x + hitbox_width/2, center_y + track_length/2 + HITBOX_PADDING, center_x, center_y, angle),
            self.calculate_rotated_point(center_x - hitbox_width/2, center_y + track_length/2 + HITBOX_PADDING, center_x, center_y, angle)
        ]
        flat_hitbox_points = [coord for point in hitbox_points for coord in point]
        self.canvas.create_polygon(flat_hitbox_points, fill="", outline="", tags=(self.tag_root, "hitbox"))

        # Track
        track_start = self.calculate_rotated_point(center_x, center_y - track_length/2, center_x, center_y, angle)
        track_end = self.calculate_rotated_point(center_x, center_y + track_length/2, center_x, center_y, angle)
        self.canvas.create_line(track_start, track_end, fill="#000000", width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(track_start, track_end, fill="#222222", width=2, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Ticks
        for i in range(TICK_COUNT):
            local_y = (center_y + track_length/2) - (track_length * (i/TICK_DIVISOR))
            tick_length = TICK_MAJOR_LENGTH if i % TICK_MAJOR_INTERVAL == 0 else TICK_MINOR_LENGTH
            tick_p1, tick_p2 = self.calculate_rotated_point(center_x-TICK_OFFSET, local_y, center_x, center_y, angle), self.calculate_rotated_point(center_x-TICK_OFFSET-tick_length, local_y, center_x, center_y, angle)
            self.canvas.create_line(tick_p1, tick_p2, fill="#666666", tags=self.tag_root)
            tick_p3, tick_p4 = self.calculate_rotated_point(center_x+TICK_OFFSET, local_y, center_x, center_y, angle), self.calculate_rotated_point(center_x+TICK_OFFSET+tick_length, local_y, center_x, center_y, angle)
            self.canvas.create_line(tick_p3, tick_p4, fill="#666666", tags=self.tag_root)

        # Cap
        norm = (self.val_current - self.val_min) / (self.val_max - self.val_min)
        local_cap_y = (center_y + track_length/2) - (norm * track_length)
        cap_center_x, cap_center_y = self.calculate_rotated_point(center_x, local_cap_y, center_x, center_y, angle)
        radius = CAP_RADIUS
        
        # Glow Effect
        outline_col = self.cap_outline_hover if self.hovered else self.cap_outline_normal
        outline_w = 3 if self.hovered else 2
        
        self.canvas.create_oval(cap_center_x-radius, cap_center_y-radius, cap_center_x+radius, cap_center_y+radius, fill=self.cap_color, outline=outline_col, width=outline_w, tags=(self.tag_root, "cap"))
        
        prad = math.radians(90 - self.rot_current - angle)
        pointer_x, pointer_y = cap_center_x + (radius-POINTER_OFFSET)*math.cos(prad), cap_center_y - (radius-POINTER_OFFSET)*math.sin(prad)
        self.canvas.create_line(cap_center_x, cap_center_y, pointer_x, pointer_y, fill=self.highlight_color, width=3, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_oval(cap_center_x-3, cap_center_y-3, cap_center_x+3, cap_center_y+3, fill=self.highlight_color, outline="", tags=self.tag_root)
        
        self.canvas.create_text(cap_center_x, cap_center_y-INDICATOR_OFFSET, text=f"{self.val_current:.1f}", fill="white", font=("Arial", 8), tags=self.tag_root)
        self.canvas.create_text(cap_center_x, cap_center_y+INDICATOR_OFFSET, text=f"R:{self.rot_current:.0f}", fill="#aaaaaa", font=("Arial", 7), tags=self.tag_root)
        self.canvas.create_text(center_x, center_y + track_length/2 + ID_LABEL_OFFSET, text=f"ID:{self.widget_id}", fill="#555555", font=("Arial", 8), tags=self.tag_root)

    def set_hover(self, state):
        if self.hovered != state:
            self.hovered = state
            self.render_visuals()

    def raise_to_top(self):
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