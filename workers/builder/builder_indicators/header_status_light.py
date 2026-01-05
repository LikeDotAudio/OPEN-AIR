import tkinter as tk
from tkinter import ttk
import orjson

class HeaderStatusLightMixin:
    """
    Adds a status indicator circle to the top-right of the GUI.
    """
    def _build_header_status_light(self, parent_widget, config): # Changed widget_config to config
        # 1. Create a Header Frame if it doesn't exist
        if not hasattr(self, 'header_frame'):
            self.header_frame = ttk.Frame(parent_widget)
            
            # Apply layout from config
            layout_config = config.get('layout', {})
            side = getattr(tk, layout_config.get('side', 'top').upper())
            fill = getattr(tk, layout_config.get('fill', 'none').upper())
            padx = layout_config.get('padx', 0)
            pady = layout_config.get('pady', 0)
            
            self.header_frame.pack(side=side, fill=fill, padx=padx, pady=pady)

        # 2. Create the Canvas for the Dot (Top Right)
        self.status_canvas = tk.Canvas(self.header_frame, width=20, height=20, bg="#F0F0F0", highlightthickness=0)
        self.status_canvas.pack(side=tk.RIGHT, padx=10)
        
        # Draw the initial circle (Gray or Red)
        self.status_light_id = self.status_canvas.create_oval(2, 2, 18, 18, fill="red", outline="white")
        
        # 3. Label (Optional) - extract from config
        label_text = config.get("label_active", "Fleet Status:") # Use label from config
        lbl = ttk.Label(self.header_frame, text=label_text, font=("Helvetica", 9))
        lbl.pack(side=tk.RIGHT, padx=5)

        # 4. Subscribe to the Monitor Worker - self.state_mirror_engine is available through self
        if self.state_mirror_engine:
                    self.state_mirror_engine.subscriber_router.subscribe_to_topic("OPEN-AIR/GUI/Global/Header/StatusLight", self._update_status_light)
                    self.state_mirror_engine.subscriber_router.subscribe_to_topic("OPENAIR/GUI/Global/Header/StatusLight", self._update_status_light)

    def _update_status_light(self, topic, payload):
        try:
            data = orjson.loads(payload)
            color = data.get("color", "red")
            
            fill_color = "#00ff00" if color == "green" else "#ff0000"
            
            # Schedule the GUI update on the main Tkinter thread
            def update_gui():
                self.status_canvas.itemconfig(self.status_light_id, fill=fill_color)
            
            if self.state_mirror_engine and self.state_mirror_engine.root:
                self.state_mirror_engine.root.after(0, update_gui)
            else:
                # Fallback if root is not accessible (shouldn't happen if properly initialized)
                self.status_canvas.itemconfig(self.status_light_id, fill=fill_color)

        except Exception as e:
            print(f"Status Light Error: {e}")
