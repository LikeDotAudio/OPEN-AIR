# radar/radar.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect
import math
import tkinter as tk

import orjson

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaComProtocols.oaComMQTT.Core import mqtt_publisher_service
from oaGui.Methods.i18n_utils import get_text
from oaGui.Workers.transparency.transparency_mixin import TransparencyMixin


class BuilderDataRadarCreator(TransparencyMixin):
    """
    Mixin for creating a Radar Eye widget.
    FIXED: Restored Background, Interaction, Grid, and Sweep.
    """

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderDataRadarCreator()
        return creator.make_data_radar(parent_widget, config_data, context, **kwargs)

    def make_data_radar(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a hierarchical radar eye widget."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️📶 [BUILDER] Entering make_data_radar", level="TRACE")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")

        label = get_text(config_data.get("label_active"), "Radar")
        path = config_data.get("path", "")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...", level="TRACE")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.", level="DEBUG")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            app_instance = kwargs.get("app_instance")
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.", level="DEBUG")

        app_settings = config_data.get("app_settings", {})
        data_parameters = config_data.get("data_parameters", {})
        visuals = config_data.get("visuals", {})
        grid_sys = config_data.get("grid_system", {})
        colors = config_data.get("color_thresholds", {})

        width = app_settings.get("window_size", [600, 600])[0]
        height = app_settings.get("window_size", [600, 600])[1]
        refresh_rate = app_settings.get("refresh_rate_ms", 33)
        mode = app_settings.get("mode", "sweep")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📐📏🔳 [LAYOUT] Radar dimensions: {width}x{height}, Mode: {mode}", level="DEBUG")

        points_count = data_parameters.get("points_per_revolution", 360)
        min_val, max_val = data_parameters.get("min_value", 0), data_parameters.get("max_value", 100)
        start_angle = data_parameters.get("start_angle", 90)
        clockwise = data_parameters.get("clockwise", True)
        plot_style = visuals.get("plot_style", "bar")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📐🔢✨ [STATE] Points: {points_count}, Range: {min_val}-{max_val}, Dir: {'CW' if clockwise else 'CCW'}", level="DEBUG")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🪟🎨 [CONSTRUCT] Creating frame and canvas for radar '{label}'", level="TRACE")
        frame = tk.Frame(parent_widget, bd=0, highlightthickness=0)
        canvas = tk.Canvas(frame, width=width, height=height, highlightthickness=0, bd=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        if hasattr(builder_instance, '_apply_transparency'):
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "👻🌀🪟 [ALPHA] Applying industrial transparency to radar.", level="TRACE")
            builder_instance._apply_transparency(frame, canvas, config_data, builder_instance)

        trig_cache = []
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "📐📏🔄 [MATH] Pre-calculating trigonometry cache for points.", level="TRACE")
        for i in range(points_count):
            offset = i * (360.0 / points_count)
            angle_deg = (start_angle - offset) if clockwise else (start_angle + offset)
            rad = math.radians(angle_deg)
            trig_cache.append((math.cos(rad), math.sin(rad)))

        radar_state = {
            "data_buffer": [min_val] * points_count,
            "current_angle_idx": 0,
            "cx": width / 2, "cy": height / 2, "radius": min(width, height) / 2 - 20,
            "trig_cache": trig_cache,
            "update_pending": False,
            "dirty_indices": set(),
            "running": True,
            "mqtt_topic": None
        }

        def get_pos(idx, r):
            c, s = radar_state["trig_cache"][idx % points_count]
            return radar_state["cx"] + r * c, radar_state["cy"] - r * s

        def get_color(v):
            mid, upper = colors.get("mid_point", 50), colors.get("upper_point", 80)
            cols = colors.get("colors", {})
            return cols.get("safe", "#00ff00") if v < mid else cols.get("warning", "#ffff00") if v < upper else cols.get("critical", "#ff0000")

        def draw_static_grid():
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔄✨🎨 [REDRAW] Drawing radar grid system.", level="TRACE")
            canvas.delete("grid")
            canvas.delete("bg")
            cx, cy, r_max = radar_state["cx"], radar_state["cy"], radar_state["radius"]

            # ⚡ INDUSTRIAL TRANSPARENCY: Don't draw patina manually, TransparencyManager handles it.
            # However, if we're NOT transparent, we might want a solid background.
            is_trans = config_data.get("transparent", False)
            if not is_trans and hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image:
                canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="bg")

            show_grid = grid_sys.get("show_grid", True)
            grid_color = grid_sys.get("grid_color", "#ffffff")
            label_cfg = grid_sys.get("labels", {})
            font_str = label_cfg.get("font", "Arial 7")
            show_values = label_cfg.get("show_values", True)

            if show_grid:
                ring_int = grid_sys.get("ring_interval", 20)
                if ring_int > 0:
                    for v in range(int(min_val), int(max_val) + 1, int(ring_int)):
                        r = ((v - min_val) / (max_val - min_val)) * r_max
                        if r > 0:
                            canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=grid_color, tags="grid")
                            if show_values:
                                canvas.create_text(cx, cy-r, text=str(v), fill=grid_color, font=font_str, tags="grid")

                spoke_int = grid_sys.get("spoke_interval", 30)
                if spoke_int > 0:
                    for a in range(0, 360, int(spoke_int)):
                        rad = math.radians(a)
                        px, py = cx + r_max * math.cos(rad), cy - r_max * math.sin(rad)
                        canvas.create_line(cx, cy, px, py, fill=grid_color, tags="grid")

            # ⚡ LAYER MANAGEMENT: Ensure grid is above background but below data
            canvas.tag_lower("grid")
            canvas.tag_lower("bg")
            # If a transparency slice exists, ensure the grid is visible on top of it
            if canvas.find_withtag("panel_bg_slice"):
                canvas.tag_raise("grid", "panel_bg_slice")

        def _schedule_draw():
            if radar_state["update_pending"]: return
            radar_state["update_pending"] = True
            canvas.after(refresh_rate, _perform_draw)

        def _perform_draw():
            radar_state["update_pending"] = False
            if plot_style in ["area", "line"]: redraw_full()
            else:
                for idx in list(radar_state["dirty_indices"]):
                    value = radar_state["data_buffer"][idx]
                    r = ((value - min_val) / (max_val - min_val)) * radar_state["radius"]
                    px, py = get_pos(idx, r)
                    tag = f"slice_{idx}"
                    items = canvas.find_withtag(tag)
                    if items: canvas.coords(items[0], radar_state["cx"], radar_state["cy"], px, py)
                    else: canvas.create_line(radar_state["cx"], radar_state["cy"], px, py, fill=get_color(value), width=2, tags=("data", tag))
                radar_state["dirty_indices"].clear()

            lx, ly = get_pos(radar_state["current_angle_idx"], radar_state["radius"])
            items = canvas.find_withtag("cursor")
            if items: canvas.coords(items[0], radar_state["cx"], radar_state["cy"], lx, ly)
            else: canvas.create_line(radar_state["cx"], radar_state["cy"], lx, ly, fill="white", width=2, tags="cursor")

        def redraw_full():
            pts = []
            if plot_style == "area": pts.extend([radar_state["cx"], radar_state["cy"]])
            for i in range(points_count + (1 if plot_style=="line" else 0)):
                v = radar_state["data_buffer"][i % points_count]
                r = ((v - min_val) / (max_val - min_val)) * radar_state["radius"]
                pts.extend(get_pos(i, r))
            if plot_style == "area": pts.extend(pts[2:4])
            tag = "data_geom"
            items = canvas.find_withtag(tag)
            if items: canvas.coords(items[0], *pts)
            else:
                if plot_style == "area": canvas.create_polygon(pts, fill="#00ff00", stipple="gray25", tags=("data", tag))
                else: canvas.create_line(pts, fill="#00ff00", width=2, tags=("data", tag))

        def on_mouse_interaction(event):
            dx, dy = event.x - radar_state["cx"], radar_state["cy"] - event.y
            r_px = math.sqrt(dx*dx + dy*dy)
            norm_r = max(0, min(1.0, r_px / radar_state["radius"]))
            new_val = min_val + (norm_r * (max_val - min_val))

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆📶 [INPUT] Radar injection: Val={new_val:.1f}", level="INFO")

            # Inject value into the variable (the system's source of truth)
            radar_value_var.set(new_val)

            if path and radar_state["mqtt_topic"]:
                payload = {"value": new_val, "pulse": True}
                mqtt_publisher_service.publish_payload(radar_state["mqtt_topic"], orjson.dumps(payload).decode())

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🖱️👆🔗 [EVENTS] Binding interaction protocols for radar eye.", level="TRACE")
        canvas.bind("<Button-2>", on_mouse_interaction)
        canvas.bind("<B2-Motion>", on_mouse_interaction)

        def sweep_loop():
            if not radar_state["running"]: return

            # ⚡ INJECTION POINT: Record the current system value into the sweep head
            idx = radar_state["current_angle_idx"]
            radar_state["data_buffer"][idx] = radar_value_var.get()
            radar_state["dirty_indices"].add(idx)

            # Move sweep head
            radar_state["current_angle_idx"] = (idx + 1) % points_count
            _schedule_draw()
            canvas.after(refresh_rate, sweep_loop)

        def perform_resize(w, h):
            if w <= 1 or h <= 1: return
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📐📏🔄 [LAYOUT] Radar performing resize to {w}x{h}.", level="DEBUG")
            radar_state.update({"cx": w/2, "cy": h/2, "radius": min(w, h)/2 - 25})

            # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
            for item in canvas.find_all():
                tags = canvas.gettags(item)
                if "panel_bg_slice" not in tags:
                    canvas.delete(item)

            draw_static_grid()
            for i in range(points_count): radar_state["dirty_indices"].add(i)
            _perform_draw()

        frame._draw = lambda: perform_resize(canvas.winfo_width(), canvas.winfo_height())
        canvas.bind("<Configure>", lambda e: frame._draw())

        radar_value_var = tk.DoubleVar(value=min_val)

        def on_value_change(*args):
            # Immediate update of the current sweep position when value changes
            idx = radar_state["current_angle_idx"]
            radar_state["data_buffer"][idx] = radar_value_var.get()
            radar_state["dirty_indices"].add(idx)
            _schedule_draw()

        radar_value_var.trace_add("write", on_value_change)

        if path:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔗 [MQTT] Registering radar eye at path '{path}'", level="TRACE")
            topic = state_mirror_engine.register_widget(path, radar_value_var, base_mqtt_topic_from_path, config_data)
            radar_state["mqtt_topic"] = topic
            if subscriber_router and topic:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Subscribing to topic: {topic}", level="DEBUG")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔄⏳🔋 [STATE] Initializing radar state from cache/broker.", level="TRACE")
            state_mirror_engine.initialize_widget_state(path)

        if mode == "sweep":
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🌀⏳🔄 [ANIM] Starting radar sweep loop.", level="TRACE")
            sweep_loop()

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗📶 [SUCCESS] The Radar Eye '{label}' has materialized!", level="SUCCESS")
        return frame
