# workers/builder/builder_radar/Builder_Radar.py

import tkinter as tk
import math
import time
import json
import random
import orjson
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service
from managers.configini.config_reader import Config

app_constants = Config.get_instance()

class RadarCreatorMixin:
    """
    Mixin for creating a Radar Eye widget.
    """

    def _create_radar(self, parent_widget, config_data, **kwargs):
        """
        Creates a Radar Eye widget based on the provided configuration.
        """
        current_function_name = "_create_radar"
        label = config_data.get("label_active", "Radar")
        path = config_data.get("path", "")
        
        # Access global context
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        # 1. Parse Configuration
        app_settings = config_data.get("app_settings", {})
        data_params = config_data.get("data_parameters", {})
        visuals = config_data.get("visuals", {})
        grid_sys = config_data.get("grid_system", {})
        colors = config_data.get("color_thresholds", {})
        conn = config_data.get("connectivity", {})

        # Defaults
        width = app_settings.get("window_size", [600, 600])[0]
        height = app_settings.get("window_size", [600, 600])[1]
        
        bg_setting = app_settings.get("background_color", "transparent")
        
        if bg_setting.lower() == "transparent":
            try:
                # Try to get parent background. Works for tk widgets.
                bg_color = parent_widget.cget("background")
            except:
                # Fallback if parent is ttk or fails
                bg_color = "#1e1e1e" 
        else:
            bg_color = bg_setting

        refresh_rate = app_settings.get("refresh_rate_ms", 50)
        mode = app_settings.get("mode", "sweep") # sweep, data_driven
        
        points_count = data_params.get("points_per_revolution", 360)
        min_val = data_params.get("min_value", 0)
        max_val = data_params.get("max_value", 100)
        start_angle = data_params.get("start_angle", 90)
        clockwise = data_params.get("clockwise", True)
        
        # Initial calculations (will be updated on resize)
        cx = width / 2
        cy = height / 2
        radius = min(width, height) / 2 - 20
        plot_style = visuals.get("plot_style", "bar") # bar, line, area

        # 2. Setup Container
        frame = tk.Frame(parent_widget, bg=bg_color)
        if label:
            lbl = tk.Label(frame, text=label, bg=bg_color, fg="white", font=("Helvetica", 10, "bold"))
            lbl.pack(side=tk.TOP, pady=(0, 5))

        # Pack canvas to fill and expand
        canvas = tk.Canvas(frame, width=width, height=height, bg=bg_color, highlightthickness=0, bd=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # 3. State Variables
        radar_state = {
            "data_buffer": [min_val] * points_count,
            "current_angle_idx": 0,
            "current_input_value": min_val, # Holds the latest value received
            "running": True
        }

        # 4. Helper Functions
        def polar_to_cartesian(angle_deg, r):
            theta_rad = math.radians(angle_deg)
            # Flip Y for screen coords (y grows down)
            x = cx + r * math.cos(theta_rad)
            y = cy - r * math.sin(theta_rad)
            return x, y

        def get_color(val):
            mid = colors.get("mid_point", 50)
            upper = colors.get("upper_point", 80)
            cols = colors.get("colors", {})
            if val < mid: return cols.get("safe", "#00ff00")
            elif val < upper: return cols.get("warning", "#ffff00")
            else: return cols.get("critical", "#ff0000")

        # 5. Drawing Functions
        def draw_static_grid():
            canvas.delete("grid")
            
            # Rings
            ring_int = grid_sys.get("ring_interval", 20)
            if ring_int > 0:
                for v in range(int(min_val), int(max_val) + 1, int(ring_int)):
                    norm = (v - min_val) / (max_val - min_val)
                    r = norm * radius
                    if r > 0:
                        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=grid_sys.get("grid_color", "#444"), tags="grid")
                        if grid_sys.get("labels", {}).get("show_values", True):
                            # Draw text only if radius is large enough to not crowd
                            if radius > 40 or (v % (ring_int*2) == 0): 
                                canvas.create_text(cx, cy - r, text=str(v), fill="#888", font=grid_sys.get("labels", {}).get("font", "Arial 8"), tags="grid")

            # Spokes
            spoke_int = grid_sys.get("spoke_interval", 30)
            if spoke_int > 0:
                for a in range(0, 360, int(spoke_int)):
                    px, py = polar_to_cartesian(a, radius)
                    canvas.create_line(cx, cy, px, py, fill=grid_sys.get("grid_color", "#444"), tags="grid")
                    
                    # Time/Angle Scale Labels
                    if grid_sys.get("labels", {}).get("show_time_scale", False):
                        if radius > 40:
                            # Draw label slightly outside
                            lx, ly = polar_to_cartesian(a, radius + 15)
                            canvas.create_text(lx, ly, text=f"{a}°", fill="#888", font=grid_sys.get("labels", {}).get("font", "Arial 8"), tags="grid")

        def update_plot_slice(idx, val):
            """Updates just the slice for bar mode."""
            step = 360.0 / points_count
            offset = idx * step
            
            if clockwise:
                angle = start_angle - offset
            else:
                angle = start_angle + offset
            
            tag = f"slice_{idx}"
            canvas.delete(tag)
            
            norm = (val - min_val) / (max_val - min_val)
            r = norm * radius
            if r <= 0: return

            color = get_color(val)
            px, py = polar_to_cartesian(angle, r)
            
            canvas.create_line(cx, cy, px, py, fill=color, width=2, tags=("data", tag))

        def redraw_full_plot():
            """Redraws the entire plot based on data buffer."""
            canvas.delete("data")
            
            if plot_style == "area":
                points = [cx, cy] # Start at center
                step = 360.0 / points_count
                
                # Order points based on rotation
                for i in range(points_count):
                    val = radar_state["data_buffer"][i]
                    offset = i * step
                    if clockwise:
                        angle = start_angle - offset
                    else:
                        angle = start_angle + offset
                    
                    norm = (val - min_val) / (max_val - min_val)
                    r = norm * radius
                    px, py = polar_to_cartesian(angle, r)
                    points.extend([px, py])
                
                # Close the loop
                points.extend(points[2:4]) 
                
                fill_col = colors.get("colors", {}).get("safe", "#00ff00")
                canvas.create_polygon(points, fill=fill_col, outline=fill_col, width=1, tags="data", stipple="gray25")
                
            elif plot_style == "line":
                # Connect dots
                prev_x, prev_y = None, None
                step = 360.0 / points_count
                
                for i in range(points_count + 1): # +1 to close loop
                    idx = i % points_count
                    val = radar_state["data_buffer"][idx]
                    
                    offset = idx * step
                    if clockwise:
                        angle = start_angle - offset
                    else:
                        angle = start_angle + offset
                        
                    norm = (val - min_val) / (max_val - min_val)
                    r = norm * radius
                    px, py = polar_to_cartesian(angle, r)
                    
                    if prev_x is not None:
                        color = get_color(val)
                        canvas.create_line(prev_x, prev_y, px, py, fill=color, width=2, tags="data")
                    
                    prev_x, prev_y = px, py
            
            elif plot_style == "bar":
                for i in range(points_count):
                    val = radar_state["data_buffer"][i]
                    update_plot_slice(i, val)

        def draw_cursor(idx):
            canvas.delete("scan_line")
            step = 360.0 / points_count
            offset = idx * step
            angle = (start_angle - offset) if clockwise else (start_angle + offset)
            lx, ly = polar_to_cartesian(angle, radius)
            canvas.create_line(cx, cy, lx, ly, fill="#FFFFFF", width=2, tags="scan_line")

        # 6. Resize Handler
        def on_resize(event):
            nonlocal cx, cy, radius
            w, h = event.width, event.height
            # Prevent division by zero or negative radius
            if w <= 1 or h <= 1: return
            
            cx = w / 2
            cy = h / 2
            # Padding of 10 for maximizing space
            radius = min(w, h) / 2 - 10
            if radius < 10: radius = 10
            
            draw_static_grid()
            redraw_full_plot()
            # Note: cursor will be redrawn on next tick

        canvas.bind("<Configure>", on_resize)

        # 7. Update Logic
        def process_update(val=None):
            if val is None:
                val = radar_state["current_input_value"]
            
            idx = radar_state["current_angle_idx"]
            radar_state["data_buffer"][idx] = val
            
            if plot_style in ["area", "line"]:
                redraw_full_plot()
            else:
                update_plot_slice(idx, val)
            
            draw_cursor(idx)
            
            # Increment
            radar_state["current_angle_idx"] = (idx + 1) % points_count

        def sweep_loop():
            if not radar_state["running"]: return
            if mode == "sweep":
                process_update()
                canvas.after(refresh_rate, sweep_loop)

        # 8. Interaction
        def clear_plot(event):
            canvas.delete("data")
            radar_state["data_buffer"] = [min_val] * points_count
            debug_logger(message=f"Radar '{label}' cleared.", **_get_log_args())

        def on_mouse_interaction(event):
            # Calculate coordinates relative to center
            dx = event.x - cx
            dy = cy - event.y # Screen Y is inverted
            
            # Calculate Radius (Value)
            r_px = math.sqrt(dx*dx + dy*dy)
            # Normalize radius to value range
            r_px = max(0, min(radius, r_px))
            norm_r = r_px / radius
            new_val = min_val + (norm_r * (max_val - min_val))
            
            # Calculate Angle (Degrees)
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            if angle_deg < 0:
                angle_deg += 360
            
            # Adjust angle based on plot orientation (optional, but good for consistency)
            # Standard atan2 is 0 at right, CCW. 
            # Radar logic might use different start/direction, but sending standard geometric angle 
            # or the specific 'scan' angle is useful. 
            # For now, we send the geometric angle (0-360 CCW from East).
            
            radar_state["current_input_value"] = new_val 
            radar_value_var.set(new_val)
            
            if path:
                # Construct richer payload
                payload = {
                    "val": new_val,
                    "angle": angle_deg,
                    "position": angle_deg,
                    "pulse": True # Explicit pulse marker
                }
                topic = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)
                # Use direct publish to send dict/JSON
                mqtt_publisher_service.publish_payload(topic, orjson.dumps(payload))
                
                # We skip state_mirror_engine.broadcast_gui_change_to_mqtt(path) 
                # because we just published manually with more data.
                # state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        canvas.bind("<Control-Button-1>", clear_plot)
        canvas.bind("<Button-2>", on_mouse_interaction)
        canvas.bind("<B2-Motion>", on_mouse_interaction)

        # 9. MQTT / Value Interface
        radar_value_var = tk.DoubleVar(value=min_val)
        
        def on_value_change(*args):
            try:
                new_val = radar_value_var.get()
                radar_state["current_input_value"] = new_val
                
                if mode == "data_driven":
                    process_update(new_val)
                    
            except: pass
            
        radar_value_var.trace_add("write", on_value_change)

        if path:
            state_mirror_engine.register_widget(path, radar_value_var, base_mqtt_topic_from_path, config_data)
            topic = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)
            subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            state_mirror_engine.initialize_widget_state(path)

        # Start
        # Initial draw handled by on_resize (which triggers on pack) 
        # But we call draw_static_grid once safely just in case
        draw_static_grid()
        
        if mode == "sweep":
            sweep_loop()
        elif mode == "data_driven":
            redraw_full_plot() if plot_style in ["area", "line"] else None
        
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(message=f"📡 Radar Eye '{label}' is ready (Mode: {mode}).", **_get_log_args())

        return frame