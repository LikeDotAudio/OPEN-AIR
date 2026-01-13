# builder_audio/dynamic_gui_create_custom_dual_horizontal_fader.py
#
# A dual horizontal fader widget that shares a single rail and outputs V1, V2, and Delta.
# The delta between V1 and V2 is highlighted.
# Handles highlight on hover and require direct grabbing to move.
# Supports mousewheel adjustment based on handle hover and middle-click reset.
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
import os
from managers.configini.config_reader import Config
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace

app_constants = Config.get_instance()

# --- Default Fader Configuration Constants ---
DEFAULT_FADER_HEIGHT = 80
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
DEFAULT_CAP_WIDTH = 30
DEFAULT_CAP_HEIGHT_RATIO = 0.6
DEFAULT_CAP_RADIUS = 10
HOVER_HANDLE_COLOR = "#444444"  # Dark grey
# ---------------------------------------------

class CustomDualHorizontalFaderFrame(tk.Frame):
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
        
        # Fader Cap Styling
        self.cap_width = int(config.get("cap_width", DEFAULT_CAP_WIDTH))
        self.cap_height_ratio = float(config.get("cap_height_ratio", DEFAULT_CAP_HEIGHT_RATIO))
        self.cap_radius = int(config.get("cap_radius", DEFAULT_CAP_RADIUS))
        self.cap_color = config.get("cap_color", self.handle_col)
        self.cap_outline_color = config.get("cap_outline_color", self.track_col)

        # Custom labels
        self.label_v1 = config.get("label_v1", "V1")
        self.label_v2 = config.get("label_v2", "V2")
        self.delta_absolute = config.get("delta_absolute", False)

        # Custom styling
        self.tick_size = config.get("tick_size", fader_style.get("tick_size", DEFAULT_TICK_SIZE_RATIO))
        tick_font_family = config.get("tick_font_family", fader_style.get("tick_font_family", DEFAULT_TICK_FONT_FAMILY))
        tick_font_size = config.get("tick_font_size", fader_style.get("tick_font_size", DEFAULT_TICK_FONT_SIZE))
        self.tick_font = (tick_font_family, tick_font_size)
        self.tick_color = config.get("tick_color", fader_style.get("tick_color", DEFAULT_TICK_COLOR))
        self.value_follow = config.get("value_follow", fader_style.get("value_follow", DEFAULT_VALUE_FOLLOW))
        self.value_highlight_color = config.get("value_highlight_color", fader_style.get("value_highlight_color", DEFAULT_VALUE_HIGHLIGHT_COLOR))
        self.value_color = config.get("value_color", self.text_col)

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

        # Initialize Variables
        self.v1_var = tk.DoubleVar(value=float(config.get("value_default_v1", (self.min_val + self.max_val)/2)))
        self.v2_var = tk.DoubleVar(value=float(config.get("value_default_v2", (self.min_val + self.max_val)/2)))
        self.delta_var = tk.DoubleVar(value=0.0)
        self._calculate_delta()

        self.temp_entry = None
        self.hovered_fader = None  # None, "V1", or "V2"
        self.active_fader = None   # None, "V1", or "V2"
        
        # Register Widgets with State Mirror Engine
        if self.state_mirror_engine and self.path:
            self._register_sub_widget("V1", self.v1_var)
            self._register_sub_widget("V2", self.v2_var)
            self._register_sub_widget("Delta", self.delta_var, read_only=True)

        # Bind traces for Delta calculation
        self.v1_var.trace_add("write", self._on_value_change)
        self.v2_var.trace_add("write", self._on_value_change)

    def _register_sub_widget(self, suffix, variable, read_only=False):
        sub_path = f"{self.path}/{suffix}"
        sub_config = self.config.copy()
        sub_config["path"] = sub_path
        
        self.state_mirror_engine.register_widget(sub_path, variable, self.base_mqtt_topic, sub_config)
        
        if not read_only:
            callback = lambda: self.state_mirror_engine.broadcast_gui_change_to_mqtt(sub_path)
            bind_variable_trace(variable, callback)
            
            topic = self.state_mirror_engine.get_widget_topic(sub_path)
            if topic:
                self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
        else:
            callback = lambda: self.state_mirror_engine.broadcast_gui_change_to_mqtt(sub_path)
            bind_variable_trace(variable, callback)
            
        self.state_mirror_engine.initialize_widget_state(sub_path)

    def _calculate_delta(self):
        v1 = self.v1_var.get()
        v2 = self.v2_var.get()
        delta = v2 - v1
        if self.delta_absolute:
            delta = abs(delta)
        self.delta_var.set(delta)

    def _on_value_change(self, *args):
        self._calculate_delta()
        self.event_generate("<<RedrawFader>>")

    def _jump_to_reff_point(self, event, target_var=None):
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"⚡ User invoked Quantum Jump! Resetting to {self.reff_point}",
                **_get_log_args(),
            )
        
        if target_var:
            target_var.set(self.reff_point)
        else:
            # If no specific target, reset both
            self.v1_var.set(self.reff_point)
            self.v2_var.set(self.reff_point)

    def _open_manual_entry(self, event, target_var):
        if self.temp_entry and self.temp_entry.winfo_exists():
            return

        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        current_val = target_var.get()
        self.temp_entry.insert(0, str(current_val))
        self.temp_entry.select_range(0, tk.END)
        self.temp_entry.focus_set()
        
        submit_cmd = lambda e: self._submit_manual_entry(e, target_var)
        self.temp_entry.bind("<Return>", submit_cmd)
        self.temp_entry.bind("<FocusOut>", submit_cmd)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    def _submit_manual_entry(self, event, target_var):
        raw_value = self.temp_entry.get()
        try:
            new_value = float(raw_value)
            if self.min_val <= new_value <= self.max_val:
                target_var.set(new_value)
            else:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Value {new_value} out of bounds! Ignoring.",
                        **_get_log_args(),
                    )
        except ValueError:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Invalid manual entry: '{raw_value}' is not a number.",
                    **_get_log_args(),
                )
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None


class CustomDualHorizontalFaderCreatorMixin:

    def _create_custom_dual_horizontal_fader(self, parent_widget, config_data, **kwargs):
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

        frame = CustomDualHorizontalFaderFrame(
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

        width = layout_config.get("width", 200)
        height = layout_config.get("height", DEFAULT_FADER_HEIGHT)

        canvas = tk.Canvas(
            frame, width=width, height=height, bg=bg_color, highlightthickness=0
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.update_idletasks()

        # Visual State
        visual_props = {"secondary": secondary_color}

        def get_x_from_val(val):
            norm_value = (
                (val - frame.min_val)
                / (frame.max_val - frame.min_val)
                if (frame.max_val - frame.min_val) != 0
                else 0
            )
            norm_value = max(0.0, min(1.0, norm_value))
            display_norm_pos = norm_value ** (1.0 / frame.log_exponent)
            return (canvas.winfo_width() - 40) * display_norm_pos + 20

        def get_handle_under_mouse(x, y):
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            cy = h / 2
            cap_w = frame.cap_width
            cap_h = h * frame.cap_height_ratio
            
            x1 = get_x_from_val(frame.v1_var.get())
            x2 = get_x_from_val(frame.v2_var.get())
            
            # Check V1
            if (x1 - cap_w/2 <= x <= x1 + cap_w/2) and (cy - cap_h/2 <= y <= cy + cap_h/2):
                return "V1"
            # Check V2
            if (x2 - cap_w/2 <= x <= x2 + cap_w/2) and (cy - cap_h/2 <= y <= cy + cap_h/2):
                return "V2"
            return None

        def on_mouse_move(event):
            handle = get_handle_under_mouse(event.x, event.y)
            if handle != frame.hovered_fader:
                frame.hovered_fader = handle
                redraw()

        def on_press(event):
            handle = get_handle_under_mouse(event.x, event.y)
            if handle:
                frame.active_fader = handle
                if event.state & 0x0004:
                    target = frame.v1_var if handle == "V1" else frame.v2_var
                    frame._jump_to_reff_point(event, target)
                elif event.state & 0x0008 or event.state & 0x0080:
                    target = frame.v1_var if handle == "V1" else frame.v2_var
                    frame._open_manual_entry(event, target)
                else:
                    update_active_fader_from_mouse(event.x)
            else:
                frame.active_fader = None

        def on_drag(event):
            if frame.active_fader:
                update_active_fader_from_mouse(event.x)

        def on_release(event):
            frame.active_fader = None
            redraw()

        def on_middle_click(event):
            handle = get_handle_under_mouse(event.x, event.y)
            if handle:
                target = frame.v1_var if handle == "V1" else frame.v2_var
                frame._jump_to_reff_point(event, target)
            else:
                frame._jump_to_reff_point(event)

        def on_mousewheel(event):
            if not frame.hovered_fader:
                return
            
            target_var = frame.v1_var if frame.hovered_fader == "V1" else frame.v2_var
            current_val = target_var.get()
            val_range = frame.max_val - frame.min_val
            step = val_range * 0.05
            
            delta = 0
            if sys.platform == "linux":
                if event.num == 4: delta = 1
                elif event.num == 5: delta = -1
            else:
                delta = 1 if event.delta > 0 else -1
            
            new_val = current_val + (delta * step)
            new_val = max(frame.min_val, min(frame.max_val, new_val))
            target_var.set(new_val)

        def update_active_fader_from_mouse(x):
            w = canvas.winfo_width()
            norm_x = (x - 20) / (w - 40)
            norm_x = max(0.0, min(1.0, norm_x))
            
            log_norm_pos = norm_x**frame.log_exponent
            current_value = frame.min_val + log_norm_pos * (
                frame.max_val - frame.min_val
            )
            
            if frame.active_fader == "V1":
                frame.v1_var.set(current_value)
            elif frame.active_fader == "V2":
                frame.v2_var.set(current_value)

        def redraw(*args):
            current_w = canvas.winfo_width()
            current_h = canvas.winfo_height()
            if current_w <= 1: current_w = width
            if current_h <= 1: current_h = height
            
            _draw_dual_fader_shared_rail(
                frame,
                canvas,
                current_w,
                current_h,
                visual_props["secondary"]
            )

        frame.bind("<<RedrawFader>>", redraw)
        
        # Initial Draw
        redraw()

        # Bindings
        canvas.bind("<Motion>", on_mouse_move)
        canvas.bind("<Button-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        canvas.bind("<Button-2>", on_middle_click)
        
        # Mousewheel Binding
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", on_mousewheel)
            canvas.bind_all("<Button-5>", on_mousewheel)
            on_mouse_move(event) # Refresh hover focus on entry

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            frame.hovered_fader = None
            redraw()

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        
        canvas.bind("<Configure>", lambda e: redraw())

        return frame

def _draw_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1,
        x2, y1, x2, y1 + radius, x2, y1 + radius, x2, y2 - radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
        x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius,
        x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)

def _draw_dual_fader_shared_rail(frame, canvas, width, height, current_secondary):
    canvas.delete("all")
    
    cy = height / 2
    
    # 1. Draw main track line
    canvas.create_line(
        20, cy, width - 20, cy,
        fill=current_secondary, width=4, capstyle=tk.ROUND
    )
    
    # 2. Calculate Handle Positions
    def get_x(val):
        norm_value = (
            (val - frame.min_val)
            / (frame.max_val - frame.min_val)
            if (frame.max_val - frame.min_val) != 0
            else 0
        )
        norm_value = max(0.0, min(1.0, norm_value))
        display_norm_pos = norm_value ** (1.0 / frame.log_exponent)
        return (width - 40) * display_norm_pos + 20

    v1_val = frame.v1_var.get()
    v2_val = frame.v2_var.get()
    x1 = get_x(v1_val)
    x2 = get_x(v2_val)
    
    # 3. Draw Delta Highlight
    canvas.create_line(
        x1, cy, x2, cy,
        fill=frame.value_highlight_color, width=6, capstyle=tk.ROUND
    )
    
    # 4. Draw Caps
    cap_width = frame.cap_width
    cap_height = height * frame.cap_height_ratio
    
    v1_col = HOVER_HANDLE_COLOR if (frame.hovered_fader == "V1" or frame.active_fader == "V1") else frame.cap_color
    v2_col = HOVER_HANDLE_COLOR if (frame.hovered_fader == "V2" or frame.active_fader == "V2") else frame.cap_color
    
    # Draw V1 Cap
    _draw_rounded_rectangle(
        canvas,
        x1 - cap_width / 2, cy - cap_height / 2,
        x1 + cap_width / 2, cy + cap_height / 2,
        radius=frame.cap_radius, fill=v1_col, outline=current_secondary
    )
    canvas.create_text(x1, cy, text=frame.label_v1, fill=frame.value_color, font=("Helvetica", 8))
    
    # Draw V2 Cap
    _draw_rounded_rectangle(
        canvas,
        x2 - cap_width / 2, cy - cap_height / 2,
        x2 + cap_width / 2, cy + cap_height / 2,
        radius=frame.cap_radius, fill=v2_col, outline=current_secondary
    )
    canvas.create_text(x2, cy, text=frame.label_v2, fill=frame.value_color, font=("Helvetica", 8))
    
    # 5. Delta Value Text
    delta_val = frame.delta_var.get()
    canvas.create_text(
        width / 2, height - 10,
        text=f"\u0394: {delta_val:.2f}",
        anchor="s",
        fill=frame.value_color,
        font=("Helvetica", 10, "bold")
    )
    
    # 6. Value Follow Labels
    if frame.value_follow:
        canvas.create_text(x1, cy - cap_height / 2 - 5, text=f"{v1_val:.1f}", fill=frame.value_color, anchor="s", font=("Helvetica", 8))
        canvas.create_text(x2, cy + cap_height / 2 + 5, text=f"{v2_val:.1f}", fill=frame.value_color, anchor="n", font=("Helvetica", 8))
