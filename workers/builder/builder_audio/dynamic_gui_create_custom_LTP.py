# builder_audio/dynamic_gui_create_custom_LTP.py
#
# A Linear Traveling Potentiometer (LTP) widget.
# Acts as a vertical fader, but the cap is a rotatable knob.
# Control + Drag rotates the knob (-100 to 100).
# Standard Drag moves the fader vertically.
# "Freestyle" mode allows adjusting both axes simultaneously (vertical=fader, horizontal=rotation).
# Grabbing the knob freezes its position (relative drag, no jump).
# Interaction restricted to handle (grabbing handle).
# Includes tick marks and mousewheel support.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk
import math
import sys
from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# --- Default Configuration Constants ---
DEFAULT_LTP_WIDTH = 100
DEFAULT_MIN_VAL = 0.0
DEFAULT_MAX_VAL = 100.0
DEFAULT_LOG_EXPONENT = 1.0
DEFAULT_BORDER_WIDTH = 0
DEFAULT_BORDER_COLOR = "black"
DEFAULT_TICK_SIZE_RATIO = 0.2
DEFAULT_TICK_FONT_FAMILY = "Helvetica"
DEFAULT_TICK_FONT_SIZE = 10
DEFAULT_TICK_COLOR = "light grey"
DEFAULT_VALUE_FOLLOW = True
DEFAULT_VALUE_HIGHLIGHT_COLOR = "#f4902c"
DEFAULT_CAP_RADIUS = 18  # Radius of the knob cap (Increased by 20% from 15)
ROTATION_MIN = -100.0
ROTATION_MAX = 100.0
# ---------------------------------------------

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.handlers.widget_event_binder import bind_variable_trace


class CustomLTPFrame(tk.Frame):
    def __init__(
        self,
        master,
        config,
        path,
        state_mirror_engine,
        base_mqtt_topic,
        subscriber_router,
    ):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        fader_style = colors.get("fader_style", {})

        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.neutral_color = colors.get("neutral", "#dcdcdc")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")
        self.text_col = colors.get("fg", "#dcdcdc")

        self.min_val = float(config.get("value_min", DEFAULT_MIN_VAL))
        self.max_val = float(config.get("value_max", DEFAULT_MAX_VAL))
        self.log_exponent = float(config.get("log_exponent", DEFAULT_LOG_EXPONENT))
        self.reff_point = float(
            config.get("reff_point", (self.min_val + self.max_val) / 2.0)
        )
        self.border_width = int(config.get("border_width", DEFAULT_BORDER_WIDTH))
        self.border_color = config.get("border_color", DEFAULT_BORDER_COLOR)
        
        # Cap Styling
        self.cap_radius = int(config.get("cap_radius", DEFAULT_CAP_RADIUS))
        self.cap_color = config.get("cap_color", self.handle_col)
        self.cap_outline_color = config.get("cap_outline_color", self.track_col)

        # Custom styling
        self.tick_size = config.get("tick_size", fader_style.get("tick_size", DEFAULT_TICK_SIZE_RATIO))
        tick_font_family = config.get("tick_font_family", fader_style.get("tick_font_family", DEFAULT_TICK_FONT_FAMILY))
        tick_font_size = config.get("tick_font_size", fader_style.get("tick_font_size", DEFAULT_TICK_FONT_SIZE))
        self.tick_font = (tick_font_family, tick_font_size)
        self.tick_color = config.get("tick_color", fader_style.get("tick_color", DEFAULT_TICK_COLOR))
        self.value_follow = config.get("value_follow", fader_style.get("value_follow", DEFAULT_VALUE_FOLLOW))
        self.value_highlight_color = config.get("value_highlight_color", fader_style.get("value_highlight_color", DEFAULT_VALUE_HIGHLIGHT_COLOR))
        self.value_color = config.get("value_color", self.text_col)
        self.ticks = config.get("ticks", None)

        super().__init__(
            master,
            bg=self.bg_color,
            bd=self.border_width,
            relief="solid",
            highlightbackground=self.border_color,
            highlightthickness=self.border_width,
        )

        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.base_mqtt_topic = base_mqtt_topic
        self.subscriber_router = subscriber_router
        self.config = config
        self.freestyle = config.get("freestyle", False)

        # Initialize Variables
        self.linear_var = tk.DoubleVar(value=float(config.get("value_default", (self.min_val + self.max_val)/2)))
        self.rotation_var = tk.DoubleVar(value=float(config.get("rotation_default", 0.0)))

        self.temp_entry = None
        
        # Register Widgets with State Mirror Engine
        if self.state_mirror_engine and self.path:
            # Register main linear variable
            self._register_sub_widget("linear", self.linear_var)
            # Register rotation variable
            self._register_sub_widget("rotation", self.rotation_var)

        # Bind traces for Redraw
        self.linear_var.trace_add("write", self._request_redraw)
        self.rotation_var.trace_add("write", self._request_redraw)

    def _register_sub_widget(self, suffix, variable):
        if suffix == "linear":
            target_path = self.path
        else:
            target_path = f"{self.path}/{suffix}"
        
        sub_config = self.config.copy()
        sub_config["path"] = target_path
        
        if suffix == "rotation":
            sub_config["value_min"] = ROTATION_MIN
            sub_config["value_max"] = ROTATION_MAX
        
        self.state_mirror_engine.register_widget(target_path, variable, self.base_mqtt_topic, sub_config)
        
        callback = lambda: self.state_mirror_engine.broadcast_gui_change_to_mqtt(target_path)
        bind_variable_trace(variable, callback)
        
        topic = self.state_mirror_engine.get_widget_topic(target_path)
        if topic:
            self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            
        self.state_mirror_engine.initialize_widget_state(target_path)

    def _request_redraw(self, *args):
        self.event_generate("<<RedrawLTP>>")

    def _open_manual_entry(self, event, target_var, min_v, max_v):
        if self.temp_entry and self.temp_entry.winfo_exists():
            return

        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        current_val = target_var.get()
        self.temp_entry.insert(0, str(current_val))
        self.temp_entry.select_range(0, tk.END)
        self.temp_entry.focus_set()
        
        submit_cmd = lambda e: self._submit_manual_entry(e, target_var, min_v, max_v)
        self.temp_entry.bind("<Return>", submit_cmd)
        self.temp_entry.bind("<FocusOut>", submit_cmd)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    def _submit_manual_entry(self, event, target_var, min_v, max_v):
        raw_value = self.temp_entry.get()
        try:
            new_value = float(raw_value)
            if min_v <= new_value <= max_v:
                target_var.set(new_value)
            else:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Value {new_value} out of bounds! Ignoring.",
                        **_get_log_args(),
                    )
        except ValueError:
            pass
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None


class CustomLTPCreatorMixin:

    def _create_custom_ltp(self, parent_widget, config_data, **kwargs):
        label = config_data.get("label_active")
        config = config_data
        path = config_data.get("path")
        
        layout_config = config.get("layout", {})
        font_size = layout_config.get("font", 10)
        custom_font = ("Helvetica", font_size)
        custom_colour = layout_config.get("colour", None)

        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        secondary_color = colors.get("secondary", "#444444")

        frame = CustomLTPFrame(
            parent_widget,
            config=config,
            path=path,
            state_mirror_engine=state_mirror_engine,
            base_mqtt_topic=base_mqtt_topic_from_path,
            subscriber_router=subscriber_router,
        )

        if label:
            lbl = tk.Label(frame, text=label, font=custom_font, background=bg_color, foreground=colors.get("fg", "#dcdcdc"))
            if custom_colour:
                lbl.configure(foreground=custom_colour)
            lbl.pack(side=tk.TOP, pady=(0, 5))

        width = layout_config.get("width", DEFAULT_LTP_WIDTH)
        height = layout_config.get("height", 300)

        canvas = tk.Canvas(
            frame, width=width, height=height, bg=bg_color, highlightthickness=0
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.update_idletasks()

        # Visual State
        visual_props = {"secondary": secondary_color}
        hover_color = "#999999"
        
        # Interaction State
        drag_state = {
            "active": False,
            "grabbing_handle": False,
            "start_x": 0, "start_y": 0,
            "start_val_lin": 0, "start_val_rot": 0,
            "last_ctrl": False
        }

        def get_handle_y(canvas_h):
            value_lin = frame.linear_var.get()
            norm_value = (
                (value_lin - frame.min_val)
                / (frame.max_val - frame.min_val)
                if (frame.max_val - frame.min_val) != 0
                else 0
            )
            norm_value = max(0.0, min(1.0, norm_value))
            display_norm_pos = norm_value ** (1.0 / frame.log_exponent)
            return (canvas_h - 40) * (1.0 - display_norm_pos) + 20

        def on_press(event):
            h = canvas.winfo_height()
            hy = get_handle_y(h)
            w = canvas.winfo_width()
            cx = w / 2
            r = frame.cap_radius
            
            if (cx - r <= event.x <= cx + r) and (hy - r <= event.y <= hy + r):
                drag_state["active"] = True
                drag_state["grabbing_handle"] = True
                drag_state["start_x"] = event.x
                drag_state["start_y"] = event.y
                drag_state["start_val_lin"] = frame.linear_var.get()
                drag_state["start_val_rot"] = frame.rotation_var.get()
                drag_state["last_ctrl"] = bool(event.state & 0x0004)
            else:
                drag_state["active"] = False
                drag_state["grabbing_handle"] = False

        def on_drag(event):
            if not drag_state["active"] or not drag_state["grabbing_handle"]:
                return
            
            h = canvas.winfo_height()
            is_ctrl = bool(event.state & 0x0004)
            
            if is_ctrl != drag_state["last_ctrl"]:
                drag_state["start_x"] = event.x
                drag_state["start_y"] = event.y
                drag_state["start_val_lin"] = frame.linear_var.get()
                drag_state["start_val_rot"] = frame.rotation_var.get()
                drag_state["last_ctrl"] = is_ctrl
            
            fader_len = h - 40
            if fader_len <= 0: fader_len = 100
            
            dx = event.x - drag_state["start_x"]
            multiplier = 2.0 if (frame.freestyle and is_ctrl) else 1.0
            
            if frame.freestyle or is_ctrl:
                rot_change = (dx / (fader_len / 2.0)) * 100.0 * multiplier
                new_rot = drag_state["start_val_rot"] + rot_change
                new_rot = max(ROTATION_MIN, min(ROTATION_MAX, new_rot))
                frame.rotation_var.set(new_rot)
            
            if frame.freestyle or not is_ctrl:
                dy = event.y - drag_state["start_y"]
                lin_range = frame.max_val - frame.min_val
                lin_change = -(dy / fader_len) * lin_range
                new_lin = drag_state["start_val_lin"] + lin_change
                new_lin = max(frame.min_val, min(frame.max_val, new_lin))
                frame.linear_var.set(new_lin)

        def on_release(event):
            drag_state["active"] = False
            drag_state["grabbing_handle"] = False

        def on_alt_click(event):
            h = canvas.winfo_height()
            hy = get_handle_y(h)
            w = canvas.winfo_width()
            cx = w / 2
            r = frame.cap_radius
            if (cx - r <= event.x <= cx + r) and (hy - r <= event.y <= hy + r):
                frame._open_manual_entry(event, frame.linear_var, frame.min_val, frame.max_val)

        def on_mousewheel(event):
            is_ctrl = bool(event.state & 0x0004)
            
            delta = 0
            if sys.platform == "linux":
                if event.num == 4: delta = 1
                elif event.num == 5: delta = -1
            else:
                delta = 1 if event.delta > 0 else -1

            if is_ctrl:
                # Adjust Rotation (Pan)
                current_rot = frame.rotation_var.get()
                rot_range = ROTATION_MAX - ROTATION_MIN
                step = rot_range * 0.05 # 5% steps
                new_rot = current_rot + (delta * step)
                new_rot = max(ROTATION_MIN, min(ROTATION_MAX, new_rot))
                frame.rotation_var.set(new_rot)
            else:
                # Adjust Linear (Volume)
                current_val = frame.linear_var.get()
                val_range = frame.max_val - frame.min_val
                step = val_range * 0.05
                
                new_val = current_val + (delta * step)
                new_val = max(frame.min_val, min(frame.max_val, new_val))
                frame.linear_var.set(new_val)

        def redraw(*args):
            current_w = canvas.winfo_width()
            current_h = canvas.winfo_height()
            if current_w <= 1: current_w = width
            if current_h <= 1: current_h = height
            
            _draw_ltp_vertical(
                frame,
                canvas,
                current_w,
                current_h,
                visual_props["secondary"]
            )

        frame.bind("<<RedrawLTP>>", redraw)
        
        # Initial Draw
        redraw()

        # Bindings
        canvas.bind("<Button-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        canvas.bind("<Alt-Button-1>", on_alt_click)
        
        # Mousewheel Binding functions
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", on_mousewheel)
            canvas.bind_all("<Button-5>", on_mousewheel)
            visual_props["secondary"] = hover_color
            redraw()

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            visual_props["secondary"] = secondary_color
            redraw()

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

        canvas.bind("<Configure>", lambda e: redraw())

        return frame

def _draw_ltp_vertical(frame, canvas, width, height, current_secondary):
    canvas.delete("all")
    cx = width / 2
    
    # 1. Track Line
    canvas.create_line(
        cx, 20, cx, height - 20,
        fill=current_secondary, width=4, capstyle=tk.ROUND
    )
    
    # 2. Draw Tick Marks
    tick_length_half = width * frame.tick_size
    tick_values = []
    if frame.ticks is not None:
        tick_values = frame.ticks
    else:
        val_range = frame.max_val - frame.min_val
        interval = 10 if val_range > 50 else 5
        if interval > 0:
            start_tick = math.ceil(frame.min_val / interval) * interval
            while start_tick <= frame.max_val:
                tick_values.append(start_tick)
                start_tick += interval

    for i, tick_value in enumerate(tick_values):
        norm_tick = (tick_value - frame.min_val) / (frame.max_val - frame.min_val) if (frame.max_val - frame.min_val) != 0 else 0
        norm_tick = max(0.0, min(1.0, norm_tick))
        display_norm_tick = norm_tick ** (1.0 / frame.log_exponent)
        tick_y = (height - 40) * (1.0 - display_norm_tick) + 20
        
        canvas.create_line(
            cx - tick_length_half, tick_y,
            cx + tick_length_half, tick_y,
            fill=frame.tick_color, width=1
        )
        if i % 2 == 0:
            canvas.create_text(
                cx + tick_length_half + 15, tick_y,
                text=str(int(tick_value)),
                fill=frame.tick_color, font=frame.tick_font, anchor="w"
            )

    # 3. Calculate Handle Position
    value_lin = frame.linear_var.get()
    norm_value = (
        (value_lin - frame.min_val)
        / (frame.max_val - frame.min_val)
        if (frame.max_val - frame.min_val) != 0
        else 0
    )
    norm_value = max(0.0, min(1.0, norm_value))
    display_norm_pos = norm_value ** (1.0 / frame.log_exponent)
    handle_y = (height - 40) * (1.0 - display_norm_pos) + 20
    
    # 4. Fill Line
    canvas.create_line(
        cx + 2.5, height - 20, cx + 2.5, handle_y,
        fill=frame.value_highlight_color, width=5, capstyle=tk.ROUND
    )
    
    # 5. Draw Rotatable Cap (Knob)
    rot_val = frame.rotation_var.get()
    angle_deg = -90 + (rot_val / 100.0) * 135.0
    angle_rad = math.radians(angle_deg)
    
    radius = frame.cap_radius
    canvas.create_oval(
        cx - radius, handle_y - radius,
        cx + radius, handle_y + radius,
        fill=frame.cap_color, outline=frame.cap_outline_color, width=2
    )
    
    # Pointer Line
    pointer_len = radius * 0.8
    px = cx + pointer_len * math.cos(angle_rad)
    py = handle_y + pointer_len * math.sin(angle_rad)
    canvas.create_line(cx, handle_y, px, py, fill=frame.cap_outline_color, width=2, capstyle=tk.ROUND)
    
    # 6. Values Text
    if frame.value_follow:
        canvas.create_text(cx + radius + 10, handle_y, text=f"{value_lin:.1f}", fill=frame.value_color, anchor="w", font=("Helvetica", 8))
        canvas.create_text(cx - radius - 10, handle_y, text=f"R:{rot_val:.0f}", fill=frame.value_color, anchor="e", font=("Helvetica", 8))