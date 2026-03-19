import tkinter as tk

class WinkSwitch:
    def __init__(self, canvas, x, y, width, height, shape="rect", 
                 bg_color="#39FF14", housing_color="#000000", 
                 radius=0, open_speed=0.08, close_speed=0.15):
        
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height if shape != "round" else width
        self.shape = shape
        self.bg_color = bg_color
        self.housing_color = housing_color # This is the "Donut" color (Black)
        
        # Physics State
        self.target_open = 0.0
        self.current_open = 0.0
        self.open_speed = open_speed
        self.close_speed = close_speed
        
        self.shutter_ids = []
        self.static_ids = []
        
        # Initialize
        self.draw_static_elements()
        self.update_visuals()

    def draw_static_elements(self):
        """Draws the bottom layer (The Color)"""
        # We draw the bright neon color first. It sits at the very bottom.
        if self.shape == "round":
            self.canvas.create_oval(self.x, self.y, self.x + self.width, self.y + self.height, 
                                    fill=self.bg_color, outline="")
        else:
            self.canvas.create_rectangle(self.x, self.y, self.x + self.width, self.y + self.height, 
                                         fill=self.bg_color, outline="")

    def update_physics(self):
        # Smooth movement logic
        if self.current_open < self.target_open:
            self.current_open = min(self.target_open, self.current_open + self.open_speed)
        elif self.current_open > self.target_open:
            self.current_open = max(self.target_open, self.current_open - self.close_speed)
        
        self.update_visuals()

    def set_pressure(self, val):
        self.target_open = max(0.0, min(1.0, float(val)))

    def update_visuals(self):
        # Clear moving parts
        for item in self.shutter_ids:
            self.canvas.delete(item)
        self.shutter_ids = []

        # 1. Calculate Shutter Positions (The "Barn Doors")
        # Even for the round switch, the mechanism is fundamentally two sliding plates.
        gap_size = self.width * self.current_open
        center_x = self.x + self.width / 2
        
        # Left and Right Shutter coordinates
        l_x2 = center_x - (gap_size / 2)
        r_x1 = center_x + (gap_size / 2)
        
        # Draw Shutters (ALWAYS BLACK) to simulate the void
        # Note: We make them slightly wider than the button to ensure they cover everything
        s1 = self.canvas.create_rectangle(self.x - 5, self.y, l_x2, self.y + self.height, 
                                          fill="black", outline="")
        s2 = self.canvas.create_rectangle(r_x1, self.y, self.x + self.width + 5, self.y + self.height, 
                                          fill="black", outline="")
        self.shutter_ids.extend([s1, s2])

        # 2. Draw the Mask/Housing (The Top Layer)
        # This covers the ugly corners of the shutters and defines the shape.
        
        if self.shape == "round":
            # THE FIX: A Pure Black "Donut"
            # We draw a very thick outline around the circle. 
            # This creates the black housing and hides the rectangular shutter corners.
            mask_thickness = 200 
            bezel = self.canvas.create_oval(
                self.x - mask_thickness/2, 
                self.y - mask_thickness/2, 
                self.x + self.width + mask_thickness/2, 
                self.y + self.height + mask_thickness/2,
                outline=self.housing_color, # BLACK
                width=mask_thickness
            )
            
            # Optional: A thin subtle grey ring just to show where the black button 
            # ends and the black background begins (if needed). 
            # I added a faint outline here for visibility.
            trim = self.canvas.create_oval(self.x, self.y, self.x+self.width, self.y+self.height,
                                           outline="#333333", width=2)
            
            self.shutter_ids.extend([bezel, trim])

        elif self.shape == "rect":
            # For rectangle, we just need top/bottom bars if we want to frame it, 
            # but usually, the shutters form the whole face. 
            # Let's add a thick black frame to represent the housing thickness.
            frame_thickness = 4
            frame = self.canvas.create_rectangle(
                self.x - frame_thickness, self.y - frame_thickness,
                self.x + self.width + frame_thickness, self.y + self.height + frame_thickness,
                outline=self.housing_color, width=frame_thickness
            )
            self.shutter_ids.append(frame)

# --- Application Setup ---

def run_app():
    root = tk.Tk()
    root.title("ITT Shadow Switch - Corrected Vis")
    
    # We use a Dark Grey background for the panel, so we can see the Black Button Housing
    panel_color = "#333333" 
    root.configure(bg=panel_color)

    # Canvas
    canvas = tk.Canvas(root, width=600, height=300, bg=panel_color, highlightthickness=0)
    canvas.pack(pady=20)

    # --- Create Switches ---
    
    # 1. The Circular One (Corrected)
    # Housing is Black. Shutters are Black. 
    # It will look like a black circle that winks green.
    sw_round = WinkSwitch(canvas, x=80, y=50, width=120, height=120, 
                          shape="round", 
                          bg_color="#39FF14",  # Neon Green
                          housing_color="black")

    # 2. The Rectangular One
    sw_rect = WinkSwitch(canvas, x=300, y=50, width=80, height=120, 
                         shape="rect", 
                         bg_color="#FF3131",   # Neon Red
                         housing_color="black")

    switches = [sw_round, sw_rect]

    # --- Controls ---
    
    lbl = tk.Label(root, text="Press and Hold / Slide to Wink", bg=panel_color, fg="white")
    lbl.pack()

    # Slider
    def on_slider(val):
        float_val = float(val) / 100
        for sw in switches:
            sw.set_pressure(float_val)

    scale = tk.Scale(root, from_=0, to=100, orient="horizontal", command=on_slider, 
                     length=400, bg="#222222", fg="white", highlightthickness=0)
    scale.pack(pady=10)
    
    # Physics Loop
    def loop():
        for sw in switches:
            sw.update_physics()
        root.after(16, loop)

    loop()
    root.mainloop()

if __name__ == "__main__":
    run_app()