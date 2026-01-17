# workers/builder/builder_radar/Builder_Radar.py

import tkinter as tk
import math
import time
import json
import random
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
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
        
        points_count = data_params.get("points_per_revolution", 360)
        min_val = data_params.get("min_value", 0)
        max_val = data_params.get("max_value", 100)
        start_angle = data_params.get("start_angle", 90)
        clockwise = data_params.get("clockwise", True)
        
        cx = visuals.get("center_x", width / 2)
        cy = visuals.get("center_y", height / 2)
        radius = visuals.get("radius", min(width, height) / 2 - 20)
        plot_style = visuals.get("plot_style", "bar")

        # 2. Setup Container
        frame = tk.Frame(parent_widget, bg=bg_color)
        if label:
            lbl = tk.Label(frame, text=label, bg=bg_color, fg="white", font=("Helvetica", 10, "bold"))
            lbl.pack(side=tk.TOP, pady=(0, 5))

        canvas = tk.Canvas(frame, width=width, height=height, bg=bg_color, highlightthickness=0)
        canvas.pack()

        # 3. State Variables
        radar_state = {
            "data_buffer": [min_val] * points_count,
            "current_angle_idx": 0,
            "current_input_value": min_val, # Holds the latest value received
            "running": True
        }

        # 4. Helper Functions
        def polar_to_cartesian(angle_deg, r):
            # Tkinter angle: 0 is Right (East), 90 is Up (North).
            # Standard Math: 0 is Right (East), CCW positive.
            # Radar logic: start_angle (90) is 0 index.
            # Clockwise means angle decreases.
            
            # Convert index/logic angle to Tkinter geometric angle
            # Logic: If 0 is at 90 deg (North)...
            # CW: 0->90, 1->(90-step), etc.
            
            theta_rad = math.radians(angle_deg)
            # Flip Y for screen coords (y grows down)
            # x = cx + r * cos(theta)
            # y = cy - r * sin(theta)  (minus because y is inverted)
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
                            canvas.create_text(cx, cy - r, text=str(v), fill="#888", font=grid_sys.get("labels", {}).get("font", "Arial 8"), tags="grid")

            # Spokes
            spoke_int = grid_sys.get("spoke_interval", 30)
            if spoke_int > 0:
                for a in range(0, 360, int(spoke_int)):
                    # Adjust for start angle and direction if needed, or just draw standard geometric spokes
                    # Usually spokes are fixed geometric
                    px, py = polar_to_cartesian(a, radius)
                    canvas.create_line(cx, cy, px, py, fill=grid_sys.get("grid_color", "#444"), tags="grid")

        def draw_data_slice(idx, val, clear=False):
            # Calculate angle for this index
            # If idx 0 is at start_angle
            step = 360.0 / points_count
            offset = idx * step
            
            if clockwise:
                angle = start_angle - offset
            else:
                angle = start_angle + offset
            
            # Clear previous slice visuals (if any specialized tag management used)
            # Here we might redraw everything or just this slice. 
            # Tkinter canvas isn't a pixel buffer, so "overwriting" means adding new items or deleting old.
            # To avoid memory leak, we should manage tags per index.
            tag = f"slice_{idx}"
            canvas.delete(tag)
            
            if clear: return

            norm = (val - min_val) / (max_val - min_val)
            r = norm * radius
            if r <= 0: return

            color = get_color(val)
            
            px, py = polar_to_cartesian(angle, r)
            
            if plot_style == "bar":
                canvas.create_line(cx, cy, px, py, fill=color, width=2, tags=("data", tag))
            elif plot_style == "line":
                # Need previous point
                pass # Complex for slice-by-slice update, simplified for bar

        # 6. Update Loop (The Sweep)
        def sweep():
            if not radar_state["running"]: return
            
            # Get current input
            val = radar_state["current_input_value"]
            idx = radar_state["current_angle_idx"]
            
            # Update history
            radar_state["data_buffer"][idx] = val
            
            # Draw
            draw_data_slice(idx, val)
            
            # Draw "Scan Line" (Cursor)
            canvas.delete("scan_line")
            step = 360.0 / points_count
            offset = idx * step
            angle = (start_angle - offset) if clockwise else (start_angle + offset)
            lx, ly = polar_to_cartesian(angle, radius)
            canvas.create_line(cx, cy, lx, ly, fill="#00ff00", width=2, tags="scan_line")
            
            # Increment
            radar_state["current_angle_idx"] = (idx + 1) % points_count
            
            canvas.after(refresh_rate, sweep)

        # 7. Interaction
        def clear_plot(event):
            canvas.delete("data")
            radar_state["data_buffer"] = [min_val] * points_count
            debug_logger(message=f"Radar '{label}' cleared.", **_get_log_args())

        def on_middle_click(event):
            # 1. Generate random valid data point
            random_val = random.uniform(min_val, max_val)
            
            # 2. Update current point in buffer and draw it
            idx = radar_state["current_angle_idx"]
            radar_state["data_buffer"][idx] = random_val
            draw_data_slice(idx, random_val)
            
            # 3. Move to next point
            radar_state["current_angle_idx"] = (idx + 1) % points_count
            
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(message=f"🎲 Radar '{label}' manual test: {random_val:.2f} at index {idx}", **_get_log_args())

        canvas.bind("<Control-Button-1>", clear_plot)
        canvas.bind("<Button-2>", on_middle_click)

        # 8. MQTT / Value Interface
        # Create a Variable to bind to MQTT
        # This variable holds the "live" value that the sweeper picks up
        radar_value_var = tk.DoubleVar(value=min_val)
        
        def on_value_change(*args):
            try:
                radar_state["current_input_value"] = radar_value_var.get()
            except: pass
            
        radar_value_var.trace_add("write", on_value_change)

        if path:
            state_mirror_engine.register_widget(path, radar_value_var, base_mqtt_topic_from_path, config_data)
            topic = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)
            subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            state_mirror_engine.initialize_widget_state(path)

        # Start
        draw_static_grid()
        sweep()
        
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(message=f"📡 Radar Eye '{label}' is scanning...", **_get_log_args())

        return frame
