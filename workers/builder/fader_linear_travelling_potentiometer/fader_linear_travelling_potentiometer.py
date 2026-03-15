# fader_linear_travelling_potentiometer/custom_LTP.py
import tkinter as tk
from tkinter import ttk
import math
import sys
import os
from PIL import Image, ImageDraw, ImageTk, ImageFilter, ImageChops

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.factory.widget_registry import WidgetRegistry

# Core Modules for Fader/Knob Rendering
from ..fader.core.scale import ScaleDrawer
from ..fader.core.track import TrackDrawer
from ..knob.core.knob_renderer import _draw_track, _draw_body, _draw_pointer

DEFAULT_LTP_WIDTH = 100
DEFAULT_MIN_VAL = 0.0
DEFAULT_MAX_VAL = 100.0
DEFAULT_LOG_EXPONENT = 1.0
DEFAULT_BORDER_WIDTH = 0
DEFAULT_BORDER_COLOR = "black"
DEFAULT_TICK_SIZE_RATIO = 0.35
DEFAULT_TICK_FONT_FAMILY = "Helvetica"
DEFAULT_TICK_FONT_SIZE = 10
DEFAULT_TICK_COLOR = "light grey"
DEFAULT_VALUE_FOLLOW = True
DEFAULT_VALUE_HIGHLIGHT_COLOR = "#f4902c"
DEFAULT_CAP_RADIUS = 18
ROTATION_MIN = -100.0
ROTATION_MAX = 100.0

# --- Module Level Cache for 3D Assets ---
_LTP_ASSET_CACHE = {}

def get_3d_ltp_knob_asset(radius, body_color, outline_color, shape="circle", teeth=12):
    """Generates a photorealistic 3D knob image for the LTP handle."""
    cache_key = (radius, body_color, outline_color, shape, teeth, "next_gen_ltp_v6")
    if cache_key in _LTP_ASSET_CACHE:
        if BUILDER_DEBUG: builder_logger.trace(f"📦🖼️✨ [CACHE] Retaining 3D LTP knob asset from cache: {radius}px")
        return _LTP_ASSET_CACHE[cache_key]

    if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D LTP knob asset: {radius}px ({body_color})")
    def hex_to_rgb(hex_str):
        if not isinstance(hex_str, str) or not hex_str.startswith("#"): return (40,40,40)
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3: hex_str = "".join([c*2 for c in hex_str])
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    b_rgb = hex_to_rgb(body_color)
    base_rgb = tuple(int(0.7 * 30 + 0.3 * c) for c in b_rgb)
    fill_col = f"#{base_rgb[0]:02x}{base_rgb[1]:02x}{base_rgb[2]:02x}"

    pad = 15
    diameter = radius * 2
    full_w, full_h = diameter + pad*2, diameter + pad*2
    base = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
    cx, cy = full_w // 2, full_h // 2
    
    def draw_shape(draw_obj, r, fill=None, outline=None, width=1, offset=(0,0)):
        ocx, ocy = cx + offset[0], cy + offset[1]
        if shape == "octagon":
            points = []
            for i in range(8):
                angle = math.radians(i * 45 + 22.5)
                points.append((ocx + r * math.cos(angle), ocy + r * math.sin(angle)))
            draw_obj.polygon(points, fill=fill, outline=outline, width=width)
        elif shape == "gear":
            points = []
            for i in range(teeth * 2):
                angle = math.radians(i * (360 / (teeth * 2)))
                curr_r = r if i % 2 == 0 else r * 0.85
                points.append((ocx + curr_r * math.cos(angle), ocy + curr_r * math.sin(angle)))
            draw_obj.polygon(points, fill=fill, outline=outline, width=width)
        else: # circle
            draw_obj.ellipse((ocx-r, ocy-r, ocx+r, ocy+r), fill=fill, outline=outline, width=width)

    # 1. Drop Shadow
    shadow = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
    s_draw = ImageDraw.Draw(shadow)
    draw_shape(s_draw, radius, fill=(0,0,0,150), offset=(4,5))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=5))
    base = Image.alpha_composite(base, shadow)
    
    # 2. Main Body
    body = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
    b_draw = ImageDraw.Draw(body)
    draw_shape(b_draw, radius, fill=fill_col, outline=outline_color, width=1)
    draw_shape(b_draw, radius-2, outline=(255,255,255,60), width=1)
    base = Image.alpha_composite(base, body)
    
    # 3. Top Face (Gloss)
    face = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
    f_draw = ImageDraw.Draw(face)
    draw_shape(f_draw, radius-4, fill=(255,255,255,15))
    base = Image.alpha_composite(base, face)

    photo = ImageTk.PhotoImage(base)
    _LTP_ASSET_CACHE[cache_key] = photo
    return photo


class CustomLTPFrame(tk.Frame):
    def __init__(self, master, config, path, state_mirror_engine, base_mqtt_topic, subscriber_router):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        fader_style = colors.get("fader_style", {})
        
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Initializing CustomLTPFrame")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config}")

        # ⚡ NESTED CONFIG SUPPORT
        f_cfg = config.get("fader_config", config)
        k_cfg = config.get("knob_config", config)
        s_cfg = config.get("style", config)
        
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")
        
        # --- Fader Parameters ---
        self.min_val = float(f_cfg.get("value_min", DEFAULT_MIN_VAL))
        self.max_val = float(f_cfg.get("value_max", DEFAULT_MAX_VAL))
        self.log_exponent = float(f_cfg.get("log_exponent", DEFAULT_LOG_EXPONENT))
        self.reff_point = float(f_cfg.get("reff_point", (self.min_val + self.max_val) / 2.0))
        self.value_highlight_color = f_cfg.get("value_highlight_color", fader_style.get("value_highlight_color", DEFAULT_VALUE_HIGHLIGHT_COLOR))
        self.show_value = bool(f_cfg.get("show_value", True))
        self.show_units = bool(f_cfg.get("show_units", False))
        self.unit_text = f_cfg.get("unit_text", "")
        self.unit_position = f_cfg.get("unit_position", "right")
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔢 [RANGE] Linear range: {self.min_val} to {self.max_val}, Log: {self.log_exponent}")
        
        # --- Knob Parameters ---
        self.rotation_min = float(k_cfg.get("rotation_min", ROTATION_MIN))
        self.rotation_max = float(k_cfg.get("rotation_max", ROTATION_MAX))
        self.cap_radius = int(k_cfg.get("cap_radius", DEFAULT_CAP_RADIUS))
        self.cap_color = k_cfg.get("cap_color", self.handle_col)
        self.cap_outline_color = k_cfg.get("cap_outline_color", self.track_col)
        self.freestyle = k_cfg.get("freestyle", config.get("freestyle", False))
        self.knob_style = k_cfg.get("knob_style", "standard")
        self.gradient_level = int(k_cfg.get("gradient_level", 0))
        if BUILDER_DEBUG: builder_logger.debug(f"🎛️🔄🔢 [RANGE] Rotation range: {self.rotation_min} to {self.rotation_max}")
        
        # --- Style Parameters ---
        self.knob_shape = s_cfg.get("knob_shape", s_cfg.get("shape", "circle"))
        self.knob_teeth = int(s_cfg.get("knob_teeth", 12))
        self.pointer_style = s_cfg.get("pointer_style", "line")
        self.arc_width = int(s_cfg.get("arc_width", 3))
        self.border_width = int(s_cfg.get("border_width", DEFAULT_BORDER_WIDTH))
        self.border_color = s_cfg.get("border_color", DEFAULT_BORDER_COLOR)
        
        # --- Scale Parameters ---
        self.custom_ticks = config.get("custom_ticks", config.get("ticks", None))
        self.tick_interval = config.get("tick_interval", None)
        self.tick_size = float(s_cfg.get("tick_size", fader_style.get("tick_size", DEFAULT_TICK_SIZE_RATIO)))
        self.tick_thickness = int(s_cfg.get("tick_thickness", fader_style.get("tick_thickness", 1)))
        self.tick_color = s_cfg.get("tick_color", fader_style.get("tick_color", DEFAULT_TICK_COLOR))
        self.sub_tick_color = s_cfg.get("sub_tick_color", self.tick_color)
        self.tick_text_color = s_cfg.get("tick_text_color", self.tick_color)
        self.sub_tick_text_color = s_cfg.get("sub_tick_text_color", self.sub_tick_color)
        self.tick_label_position = str(s_cfg.get("tick_label_position", "right")).lower()
        
        t_font_family = s_cfg.get("tick_font_family", fader_style.get("tick_font_family", DEFAULT_TICK_FONT_FAMILY))
        t_font_size = int(s_cfg.get("tick_font_size", fader_style.get("tick_font_size", DEFAULT_TICK_FONT_SIZE)))
        self.tick_font = (t_font_family, t_font_size)

        self.value_follow = s_cfg.get("value_follow", fader_style.get("value_follow", DEFAULT_VALUE_FOLLOW))
        self.value_color = s_cfg.get("value_color", self.accent_color)
        self.label_color = s_cfg.get("label_color", "white")
        self.track_hover_color = s_cfg.get("track_hover_color", "#444444")

        super().__init__(master, bd=self.border_width, relief="solid", highlightbackground=self.border_color, highlightthickness=self.border_width)
        
        self.path, self.state_mirror_engine, self.base_mqtt_topic, self.subscriber_router = path, state_mirror_engine, base_mqtt_topic, subscriber_router
        self.widget_config, self.orientation = config, "vertical"
        
        initial_lin = f_cfg.get("value_default", f_cfg.get("value", self.reff_point))
        initial_rot = k_cfg.get("rotation_default", k_cfg.get("rotation", 0.0))
        self.linear_var = tk.DoubleVar(value=float(initial_lin))
        self.rotation_var = tk.DoubleVar(value=float(initial_rot))
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🎚️🎛️ [STATE] Initial values: Lin={self.linear_var.get()}, Rot={self.rotation_var.get()}")
        
        self.is_sliding = False
        self.is_hovered = False
        self.temp_entry = None
        self.linear_var.trace_add("write", self._request_redraw)
        self.rotation_var.trace_add("write", self._request_redraw)

    def _request_redraw(self, *args): 
        if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🎨 [REDRAW] Redraw event triggered for LTP '{self.path}'")
        try: self.event_generate("<<RedrawLTP>>", when="tail")
        except: pass

    def _open_manual_entry(self, event, target_var, min_v, max_v):
        if BUILDER_DEBUG: builder_logger.debug(f"📝⌨️🖱️ [INPUT] Opening manual entry for LTP member at ({event.x}, {event.y})")
        if self.temp_entry and self.temp_entry.winfo_exists(): return
        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        self.temp_entry.insert(0, str(target_var.get()))
        self.temp_entry.select_range(0, tk.END); self.temp_entry.focus_set()
        submit_cmd = lambda e: self._submit_manual_entry(e, target_var, min_v, max_v)
        self.temp_entry.bind("<Return>", submit_cmd); self.temp_entry.bind("<FocusOut>", submit_cmd); self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    def _submit_manual_entry(self, event, target_var, min_v, max_v):
        try:
            val_str = self.temp_entry.get()
            val = float(val_str)
            if min_v <= val <= max_v:
                if BUILDER_DEBUG: builder_logger.info(f"🆗✅🔢 [INPUT] Manual entry accepted: {val} for LTP '{self.path}'")
                target_var.set(val)
                if self.path and self.state_mirror_engine: 
                    p = self.path if target_var == self.linear_var else f"{self.path}.rotation"
                    if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Broadcasting manual entry for component: {p}")
                    self.state_mirror_engine.broadcast_gui_change_to_mqtt(p)
            else:
                if BUILDER_DEBUG: builder_logger.warning(f"⚠️❌🚫 [INPUT] Manual entry {val} out of range for component.")
        except ValueError:
            if BUILDER_DEBUG: builder_logger.warning(f"⚠️❌🔡 [INPUT] Invalid manual entry '{val_str}' for LTP.")
            pass
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            if BUILDER_DEBUG: builder_logger.trace(f"❌🧹🖱️ [INPUT] Closing manual entry for LTP.")
            self.temp_entry.destroy(); self.temp_entry = None


@WidgetRegistry.register("_CustomLTP")
class BuilderFaderLinearTravellingPotentiometerCreator(TransparencyMixin):
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating an LTP widget.
        """
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Entering BuilderFaderLinearTravellingPotentiometerCreator.make")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        config, path, label = config_data, config_data.get("path"), config_data.get("label_active")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🎚️ [BUILDER] Spawning Linear Travelling Potentiometer for '{label}' at path '{path}'.")

        frame = CustomLTPFrame(parent_widget, config, path, state_mirror_engine, base_mqtt_topic_from_path, subscriber_router)
        
        if path:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering dual-variable state for path '{path}'")
            # ⚡ FLATTEN CONFIG: Ensure StateMirrorEngine sees min/max at the top level
            # to avoid clamping negative values to the default 0.0
            lin_config = {**config, **config.get("fader_config", {})}
            topic = state_mirror_engine.register_widget(path, frame.linear_var, base_mqtt_topic_from_path, lin_config)
            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing LINEAR to topic: {topic}")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing LINEAR state from cache/broker.")
            state_mirror_engine.initialize_widget_state(path)
            
            rot_path = f"{path}.rotation"
            # Explicitly pass min/max for rotation as well
            rot_config = {**config, **config.get("knob_config", {}), "path": rot_path, "value_min": frame.rotation_min, "value_max": frame.rotation_max}
            rot_topic = state_mirror_engine.register_widget(rot_path, frame.rotation_var, base_mqtt_topic_from_path, rot_config)
            if subscriber_router and rot_topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing ROTATION to topic: {rot_topic}")
                subscriber_router.subscribe_to_topic(rot_topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing ROTATION state from cache/broker.")
            state_mirror_engine.initialize_widget_state(rot_path)

        if BUILDER_DEBUG: builder_logger.trace("🏗️🪟🖼️ [CONSTRUCT] Creating main LTP canvas.")
        canvas = tk.Canvas(frame, width=config.get("layout", {}).get("width", DEFAULT_LTP_WIDTH), height=config.get("layout", {}).get("height", 300), highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        if hasattr(builder_instance, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to LTP components.")
            builder_instance._apply_transparency(frame, canvas, config, builder_instance)
        
        def sync_bg(): redraw()
        frame._draw = sync_bg

        drag_state = {"active": False, "grabbing_handle": False, "start_x": 0, "start_y": 0, "start_val_lin": 0, "start_val_rot": 0, "last_ctrl": False}
        
        def get_handle_pos(length):
            norm = max(0.0, min(1.0, (frame.linear_var.get() - frame.min_val) / (frame.max_val - frame.min_val))) if (frame.max_val - frame.min_val) != 0 else 0
            d_norm = norm ** (1.0 / frame.log_exponent)
            padding_edge = 25 # Reserve space for labels/ticks
            return (length - 50) * (1.0 - d_norm if frame.orientation == "vertical" else d_norm) + padding_edge

        def on_press(event):
            w, h, r = canvas.winfo_width(), canvas.winfo_height(), frame.cap_radius
            h_pos = get_handle_pos(h if frame.orientation == "vertical" else w)
            if frame.orientation == "vertical": in_zone = (w/2 - r <= event.x <= w/2 + r) and (h_pos - r <= event.y <= h_pos + r)
            else: in_zone = (h_pos - r <= event.x <= h_pos + r) and (h/2 - r <= event.y <= h/2 + r)
            
            # Interaction: Clicking anywhere on the track moves linear value
            if not in_zone:
                set_linear_from_event(event)
            
            drag_state.update({"active": True, "grabbing_handle": True, "start_x": event.x, "start_y": event.y, "start_val_lin": frame.linear_var.get(), "start_val_rot": frame.rotation_var.get(), "last_ctrl": bool(event.state & 0x0004)})
            frame.is_sliding = True

        def set_linear_from_event(event):
            w, h = canvas.winfo_width(), canvas.winfo_height()
            if frame.orientation == "vertical":
                norm = max(0.0, min(1.0, (event.y - 25) / (h - 50)))
                norm = 1.0 - norm
            else:
                norm = max(0.0, min(1.0, (event.x - 25) / (w - 50)))
            val = frame.min_val + (norm ** frame.log_exponent) * (frame.max_val - frame.min_val)
            frame.linear_var.set(val)
            if path and state_mirror_engine: state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        def on_drag(event):
            if not drag_state["active"]: return
            w, h, is_ctrl = canvas.winfo_width(), canvas.winfo_height(), bool(event.state & 0x0004)
            if is_ctrl != drag_state["last_ctrl"]: drag_state.update({"start_x": event.x, "start_y": event.y, "start_val_lin": frame.linear_var.get(), "start_val_rot": frame.rotation_var.get(), "last_ctrl": is_ctrl})
            dx, dy = event.x - drag_state["start_x"], event.y - drag_state["start_y"]
            mult = 2.0 if (frame.freestyle and is_ctrl) else 1.0
            flen = (h if frame.orientation == "vertical" else w) - 50
            
            if frame.orientation == "vertical":
                if frame.freestyle or is_ctrl: 
                    new_rot = drag_state["start_val_rot"] + (dx / (flen/2)) * 100 * mult
                    frame.rotation_var.set(max(frame.rotation_min, min(frame.rotation_max, new_rot)))
                if frame.freestyle or not is_ctrl: 
                    new_lin = drag_state["start_val_lin"] - (dy / flen) * (frame.max_val - frame.min_val)
                    frame.linear_var.set(max(frame.min_val, min(frame.max_val, new_lin)))
            else:
                if frame.freestyle or is_ctrl: 
                    new_rot = drag_state["start_val_rot"] - (dy / (h/2)) * 100 * mult
                    frame.rotation_var.set(max(frame.rotation_min, min(frame.rotation_max, new_rot)))
                if frame.freestyle or not is_ctrl: 
                    new_lin = drag_state["start_val_lin"] + (dx / flen) * (frame.max_val - frame.min_val)
                    frame.linear_var.set(max(frame.min_val, min(frame.max_val, new_lin)))
            
            if path and state_mirror_engine: 
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                state_mirror_engine.broadcast_gui_change_to_mqtt(f"{path}.rotation")

        def redraw(*args):
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            if cw <= 1: cw, ch = config.get("layout", {}).get("width", DEFAULT_LTP_WIDTH), config.get("layout", {}).get("height", 300)
            frame.orientation = "horizontal" if cw > ch else "vertical"
            
            # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
            for item in canvas.find_all():
                tags = canvas.gettags(item)
                if "panel_bg_slice" not in tags:
                    canvas.delete(item)
            
            # 0. Draw Industrial Background (Fallback if slice doesn't exist)
            if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
                canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
            cx, cy = cw / 2.0, ch / 2.0
            top_res, bot_res = 25.0, 25.0
            
            if frame.orientation == "vertical":
                # Draw Recessed Track
                TrackDrawer.draw(canvas, frame, cx, top_res, ch, 10, hover_color=frame.track_hover_color if frame.is_hovered else None)
                # Draw Scale (Ticks & Labels)
                f_h = ch - top_res - bot_res
                ScaleDrawer.draw(canvas, frame, cw, ch, cx, f_h, top_res, cw * frame.tick_size, 10, cap_width=frame.cap_radius*2)
                
                # Active Highlight
                h_pos = get_handle_pos(ch)
                canvas.create_line(cx, ch - bot_res, cx, h_pos, fill=frame.value_highlight_color, width=2, capstyle=tk.ROUND, tags="fill_line")
                BuilderFaderLinearTravellingPotentiometerCreator._draw_ltp_knob(canvas, cx, h_pos, frame)
            else:
                # Horizontal Mode
                # Slot
                canvas.create_rectangle(25, cy - 5, cw - 25, cy + 5, fill="#0a0a0a", outline="#333", width=1, tags="static")
                
                # Basic Ticks for Horizontal (Simplified for now)
                val_range = frame.max_val - frame.min_val
                if val_range != 0:
                    ti = frame.tick_interval or (val_range / 10)
                    if ti > 0:
                        curr = math.ceil(frame.min_val / ti) * ti
                        while curr <= frame.max_val:
                            norm = (curr - frame.min_val) / val_range
                            tx = 25 + norm * (cw - 50)
                            canvas.create_line(tx, cy + 15, tx, cy + 25, fill=frame.tick_color, tags="static")
                            curr += ti

                h_pos = get_handle_pos(cw)
                canvas.create_line(25, cy, h_pos, cy, fill=frame.value_highlight_color, width=2, capstyle=tk.ROUND, tags="fill_line")
                BuilderFaderLinearTravellingPotentiometerCreator._draw_ltp_knob(canvas, h_pos, cy, frame)

            if label: 
                canvas.create_text(cw/2, 10, text=label, fill=config.get("layout", {}).get("colour", "#dcdcdc"), 
                                   font=("Helvetica", config.get("layout", {}).get("font", 10), "bold"), anchor="n", tags="industrial_text")

        def on_mousewheel(event):
            # ⚡ LTP Scroll: Adjusts ROTATION for high-precision control
            curr_rot = frame.rotation_var.get()
            rot_range = frame.rotation_max - frame.rotation_min
            step = rot_range * 0.02 # 2% step per notch
            
            delta = 1 if (event.num == 4 or event.delta > 0) else -1
            if sys.platform == "linux" and event.num == 5: delta = -1
            
            new_rot = max(frame.rotation_min, min(frame.rotation_max, curr_rot + (delta * step)))
            frame.rotation_var.set(new_rot)
            if path and state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(f"{path}.rotation")
            
            # Temporary hover state for visual feedback
            frame.is_sliding = True
            canvas.after(500, lambda: setattr(frame, 'is_sliding', False) or redraw())

        canvas.bind("<Enter>", lambda e: setattr(frame, 'is_hovered', True) or redraw())
        canvas.bind("<Leave>", lambda e: setattr(frame, 'is_hovered', False) or redraw())
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)
        canvas.bind("<Button-5>", on_mousewheel)
        frame.bind("<<RedrawLTP>>", redraw)
        canvas.bind("<Button-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", lambda e: drag_state.update({'active': False}) or setattr(frame, 'is_sliding', False) or redraw())
        
        def on_middle_click(event):
            # Reset both linear and rotation state
            frame.linear_var.set(frame.reff_point)
            frame.rotation_var.set(0.0) # Standard reset for rotation
            if path and state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                state_mirror_engine.broadcast_gui_change_to_mqtt(f"{path}.rotation")
            redraw()

        canvas.bind("<Button-2>", on_middle_click)
        canvas.bind("<Alt-Button-1>", lambda e: frame._open_manual_entry(e, frame.linear_var, frame.min_val, frame.max_val))
        canvas.bind("<Configure>", lambda e: redraw())
        
        redraw(); return frame

    def make_fader_linear_travelling_potentiometer(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderLinearTravellingPotentiometerCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)

    @staticmethod
    def _draw_ltp_knob(canvas, cx, cy, frame):
        knob_img = get_3d_ltp_knob_asset(frame.cap_radius, frame.cap_color, frame.cap_outline_color, shape=frame.knob_shape, teeth=frame.knob_teeth)
        canvas.create_image(cx, cy, image=knob_img, tags="fader_cap")
        canvas.knob_img = knob_img
        
        norm = (frame.rotation_var.get() - frame.rotation_min) / (frame.rotation_max - frame.rotation_min) if frame.rotation_max > frame.rotation_min else 0
        start, ext = (240, -300 * norm)
        _draw_pointer(canvas, cx, cy, frame.cap_radius, frame.arc_width, start+ext, frame.pointer_style, frame.cap_outline_color, frame.cap_radius * 0.8, 0, False)
        
        if frame.is_sliding and frame.value_follow:
            txt = f"{frame.linear_var.get():.1f}"
            canvas.create_text(cx, cy - frame.cap_radius - 10, text=txt, fill=frame.value_color, font=("Arial", 8, "bold"), tags="floating_val")
