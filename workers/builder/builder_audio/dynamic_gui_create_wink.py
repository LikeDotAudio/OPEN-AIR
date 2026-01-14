# builder_audio/dynamic_gui_create_wink.py
import tkinter as tk
from tkinter import ttk
import time
from managers.configini.config_reader import Config
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME

app_constants = Config.get_instance()

class WinkButtonCreatorMixin:
    """
    A mixin to create 'Wink' style buttons/switches.
    Mimics a mechanical shutter revealing a bright background.
    Improved with bezel masking for perfect round shapes and rounded rectangles.
    """

    def _create_wink_button(self, parent_widget, config_data, **kwargs):
        """Creates a Wink Button widget."""
        
        # Extract config
        label = config_data.get("label_active")
        config = config_data
        path = config_data.get("path")
        
        # Appearance Parameters
        shape_type = config.get("shape_type", "rect").lower() # 'round', 'square', 'rect'
        width = config.get("width", 60)
        height = config.get("height", 60) if shape_type != "round" else width
        radius = config.get("radius", 5) # Default radius for rect/square
        
        bg_color = config.get("color", "#39FF14") # Neon background
        
        # Determine Bezel Color (Mask Color)
        theme_colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        default_bg = theme_colors.get("bg", "#2b2b2b")
        bezel_color = config.get("bezel_color", default_bg) 
        
        # Shutter Settings
        shutter_color = config.get("shutter_color", "black")
        text_closed = config.get("text_closed", "")
        text_closed_color = config.get("text_closed_color", "white" if shutter_color == "black" else "black")
        
        # Border/Outline Settings
        border_thickness = config.get("border_thickness", 2)
        border_color = "black" # Always black as requested
        
        # Text Inside
        text_inside = config.get("text_inside", "")
        text_inside_color = config.get("text_inside_color", "black")
        
        # Logic Parameters
        is_latching = config.get("latching", False)

        # Physics Parameters
        open_speed = config.get("open_speed", 0.15)
        close_speed = config.get("close_speed", 0.3)
        
        # Container Frame
        frame = ttk.Frame(parent_widget)
        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        # Canvas
        canvas = tk.Canvas(
            frame, 
            width=width, 
            height=height, 
            bg=bezel_color, 
            highlightthickness=0
        )
        canvas.pack()
        
        # --- State Management ---
        # value_var tracks the logical state (for MQTT/Application)
        initial_value = config.get("value_default", False)
        value_var = tk.BooleanVar(value=initial_value)

        # Internal state for physics and latching logic
        state = {
            "target_open": 1.0 if initial_value else 0.0,
            "current_open": 1.0 if initial_value else 0.0,
            "is_pressed": False,
            "is_latched": initial_value,
            "shutter_ids": [],
            "animating": False
        }

        def _create_rounded_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
            """Helper to draw a rounded rectangle."""
            points = [
                x1 + radius, y1,
                x1 + radius, y1,
                x2 - radius, y1,
                x2 - radius, y1,
                x2, y1,
                x2, y1 + radius,
                x2, y1 + radius,
                x2, y2 - radius,
                x2, y2 - radius,
                x2, y2,
                x2 - radius, y2,
                x2 - radius, y2,
                x1 + radius, y2,
                x1 + radius, y2,
                x1, y2,
                x1, y2 - radius,
                x1, y2 - radius,
                x1, y1 + radius,
                x1, y1 + radius,
                x1, y1
            ]
            return canvas.create_polygon(points, smooth=True, **kwargs)

        def update_physics():
            """Smoothly interpolates current position to target position."""
            current = state["current_open"]
            target = state["target_open"]
            
            moved = False
            if current < target:
                state["current_open"] += open_speed
                if state["current_open"] > target:
                    state["current_open"] = target
                moved = True
            elif current > target:
                state["current_open"] -= close_speed
                if state["current_open"] < target:
                    state["current_open"] = target
                moved = True
            
            if moved:
                draw_visuals()
            
            if moved or state["is_pressed"] or state["current_open"] != target:
                canvas.after(16, update_physics)
            else:
                state["animating"] = False

        def draw_visuals():
            """Redraws the moving parts (shutters) and the top bezel mask."""
            for item in state["shutter_ids"]:
                canvas.delete(item)
            state["shutter_ids"] = []

            # 1. Background Neon Light
            if shape_type == "round":
                neon = canvas.create_oval(0, 0, width, height, fill=bg_color, outline="")
                state["shutter_ids"].append(neon)
            else:
                neon = _create_rounded_rect(canvas, 0, 0, width, height, radius=radius, fill=bg_color, outline="")
                state["shutter_ids"].append(neon)

            # 1.5 Text Inside (Drawn on top of neon, covered by shutters)
            if text_inside:
                # Calculate font size roughly based on height
                font_size = int(height * 0.25)
                text_item = canvas.create_text(
                    width / 2, 
                    height / 2, 
                    text=text_inside, 
                    fill=text_inside_color,
                    font=("Arial", font_size, "bold"),
                    anchor="center"
                )
                state["shutter_ids"].append(text_item)

            # 2. Shutters (Rectangular, configurable color)
            gap_size = width * state["current_open"]
            center_x = width / 2
            
            l_shutter_x2 = center_x - (gap_size / 2)
            r_shutter_x1 = center_x + (gap_size / 2)

            s1 = canvas.create_rectangle(0, 0, l_shutter_x2, height, fill=shutter_color, outline="")
            s2 = canvas.create_rectangle(r_shutter_x1, 0, width, height, fill=shutter_color, outline="")
            state["shutter_ids"].extend([s1, s2])
            
            # 2.5 Text Closed (Drawn on shutters, moves with them)
            if text_closed:
                font_size_closed = int(height * 0.25)
                # We draw the full text on BOTH shutters, but we need to clip it? 
                # Tkinter canvas text doesn't support clipping easily.
                # Hack: Draw the text at the center relative to the shutter's movement.
                # Left Shutter: Text is at (width/2) - (gap_size/2).
                # Right Shutter: Text is at (width/2) + (gap_size/2).
                # But we want the text to "break".
                # So "CLOSED" becomes "CLO" (left) and "SED" (right)?
                # Or simply: The text is painted on the shutter surface.
                # Center of text was at center of canvas (width/2).
                # Now that point has moved left by gap_size/2.
                
                # Left Half Text
                # Draw text shifted left
                t1 = canvas.create_text(
                    (width / 2) - (gap_size / 2), 
                    height / 2,
                    text=text_closed,
                    fill=text_closed_color,
                    font=("Arial", font_size_closed, "bold"),
                    anchor="center"
                )
                
                # Right Half Text
                # Draw text shifted right
                t2 = canvas.create_text(
                    (width / 2) + (gap_size / 2), 
                    height / 2,
                    text=text_closed,
                    fill=text_closed_color,
                    font=("Arial", font_size_closed, "bold"),
                    anchor="center"
                )
                
                # Masking hack:
                # We need the left text to be invisible on the right side, and vice versa.
                # We can't easily mask.
                # BUT, the gap is empty (showing neon).
                # The text should physically move.
                # If we just draw the text moving, it looks like two copies moving apart.
                # Which is exactly what "text painted on split doors" looks like if you ignore the cut.
                # The cut "eats" the middle letters? No.
                # The cut splits the letters.
                # Realistically, the text is cut in half.
                # "O" becomes "(" and ")".
                # For this prototype, moving the whole text apart is a decent approximation 
                # effectively duplicating the text, but the visual brain might accept it 
                # if the gap is obvious.
                # A better trick: Use a "Gap Mask".
                # We don't have one.
                # Let's stick to the "Two Copies Moving" effect. It conveys the idea.
                state["shutter_ids"].extend([t1, t2])

            # 3. Bezel / Detail Ring
            if shape_type == "round":
                # Doughnut mask
                mask_thickness = max(width, height) 
                bezel = canvas.create_oval(
                    -mask_thickness/2, 
                    -mask_thickness/2, 
                    width + mask_thickness/2, 
                    height + mask_thickness/2,
                    outline=bezel_color,
                    width=mask_thickness
                )
                # Border Ring
                ring = canvas.create_oval(
                    border_thickness/2, border_thickness/2, 
                    width-border_thickness/2, height-border_thickness/2, 
                    outline=border_color, width=border_thickness
                )
                state["shutter_ids"].extend([bezel, ring])
            else:
                # Rounded Rect Bezel Border (Outline)
                border = _create_rounded_rect(
                    canvas, 
                    border_thickness/2, border_thickness/2, 
                    width-border_thickness/2, height-border_thickness/2, 
                    radius=radius, 
                    outline=border_color, 
                    width=border_thickness, 
                    fill=""
                )
                state["shutter_ids"].append(border)


        # --- MQTT and State Mirroring ---
        def on_value_change(*args):
            """Called when value_var changes (programmatically or via UI)."""
            new_val = value_var.get()
            
            # Update Physics Target
            state["target_open"] = 1.0 if new_val else 0.0
            
            # Sync Latch State (if updated remotely), but ONLY if not locally pressed
            if is_latching and not state["is_pressed"]:
                state["is_latched"] = new_val

            # Trigger Animation
            if not state["animating"]:
                state["animating"] = True
                update_physics()

            # Broadcast
            if self.state_mirror_engine:
                 self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        # Trace the variable
        value_var.trace_add("write", on_value_change)

        # Register with Engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if path and self.state_mirror_engine:
            widget_id = path
            self.state_mirror_engine.register_widget(
                widget_id, value_var, base_mqtt_topic_from_path, config
            )

            # Subscribe to incoming messages
            from workers.mqtt.mqtt_topic_utils import get_topic
            topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id)
            self.subscriber_router.subscribe_to_topic(
                topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
            )
            
            # Initialize
            state_mirror_engine = self.state_mirror_engine
            state_mirror_engine.initialize_widget_state(path)


        # Input Handling
        def on_press(event):
            state["is_pressed"] = True
            # Pressing always forces True (Open)
            value_var.set(True) 

        def on_release(event):
            state["is_pressed"] = False
            
            if is_latching:
                # Toggle logic:
                # We simply toggle the persistent state.
                state["is_latched"] = not state["is_latched"]
                value_var.set(state["is_latched"])
            else:
                value_var.set(False)

        def on_enter(event):
            state["is_hovering"] = True
            draw_visuals()

        def on_leave(event):
            state["is_hovering"] = False
            draw_visuals()

        canvas.bind("<Button-1>", on_press)
        canvas.bind("<ButtonRelease-1>", on_release)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        
        draw_visuals()

        return frame
