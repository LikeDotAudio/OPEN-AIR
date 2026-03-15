# fader/dynamic_guimake_fader.py
#
# A vertical fader widget that adapts to the system theme.
# Includes mousewheel support and middle-click reset.
# OPTIMIZED: Decoupled movement from heavy static rendering.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260220.Modular.5

import tkinter as tk
from tkinter import ttk
import math
import sys
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

# Modular Core Components
from workers.builder.fader.core.scale import ScaleDrawer
from workers.builder.fader.core.track import TrackDrawer
from workers.builder.fader.core.readout import ReadoutDrawer
from workers.builder.fader.core.cap import CapDrawer

class CustomFaderFrame(tk.Frame):
    def __init__(self, master, variable, config, path, state_mirror_engine, command):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        fader_style = colors.get("fader_style", {})
        
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.neutral_color = colors.get("neutral", "#dcdcdc")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")

        self.min_val = float(config.get("value_min", -100.0))
        self.max_val = float(config.get("value_max", 0.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(config.get("reff_point", (self.min_val + self.max_val) / 2.0))
        self.border_width = int(config.get("border_width", 0))
        self.border_color = config.get("border_color", "black")
        self.show_value = bool(config.get("show_value", True))
        self.show_units = bool(config.get("show_units", False))
        self.label_color = config.get("label_color", "white")
        self.value_color = config.get("value_color", "white")
        self.label_text = config.get("label_active", "")
        
        self.custom_ticks = config.get("custom_ticks", config.get("ticks", None))
        self.tick_interval = config.get("tick_interval", None)
        self.tick_color = config.get("tick_color", config.get("scale_colour_tick", fader_style.get("tick_color", "light grey")))
        self.sub_tick_color = config.get("sub_tick_color", self.tick_color) 
        self.tick_text_color = config.get("tick_text_color", self.tick_color)
        self.sub_tick_text_color = config.get("sub_tick_text_color", self.sub_tick_color)
        self.tick_label_position = str(config.get("tick_label_position", "right")).lower()

        self.cap_color = config.get("cap_color", config.get("cap", self.handle_col))
        self.cap_highlight_color = config.get("cap_highlight_color", config.get("cap_highlights", None))
        self.track_hover_color = config.get("track_hover_color", "#444444") 

        self.tick_size = float(config.get("tick_size", fader_style.get("tick_size", 0.35)))
        self.tick_thickness = int(config.get("tick_thickness", fader_style.get("tick_thickness", 1)))
        tick_font_family = config.get("tick_font_family", fader_style.get("tick_font_family", "Helvetica"))
        tick_font_size = int(config.get("tick_font_size", fader_style.get("tick_font_size", 10)))
        self.tick_font = (tick_font_family, tick_font_size)
        
        self.unit_text = config.get("unit_text", "")
        self.unit_color = config.get("unit_color", self.value_color)
        self.unit_position = config.get("unit_position", "right") 

        self.value_follow = bool(config.get("value_follow", fader_style.get("value_follow", True)))
        self.movement_value_display = bool(config.get("movement_value_display", True))
        self.value_highlight_color = config.get("value_highlight_color", fader_style.get("value_highlight_color", "#f4902c"))
        
        self.fader_track_color = config.get("fader_track_color", config.get("fader_colour", self.track_col))
        self.fader_grip_color = config.get("fader_grip_color", self.handle_col)
        
        self.cap_width_override = config.get("cap_width")
        self.cap_height_override = config.get("cap_height")
        self.fader_cap_scale = float(config.get("fader_cap_scale", 1.0))

        self.is_sliding = False
        self.is_locked = False # ⚡ INTERACTION LOCK
        self.is_hovered = False

        super().__init__(
            master,
            bd=self.border_width,
            relief="solid",
            highlightbackground=self.border_color,
            highlightthickness=self.border_width,
            bg=self.bg_color
        )
        self.variable = variable
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.command = command
        self.temp_entry = None

    def _jump_to_reff_point(self, event):
        self.variable.set(self.reff_point)
        if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _open_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists(): return
        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        self.temp_entry.insert(0, str(self.variable.get()))
        self.temp_entry.select_range(0, tk.END)
        self.temp_entry.focus_set()
        self.temp_entry.bind("<Return>", self._submit_manual_entry)
        self.temp_entry.bind("<FocusOut>", self._submit_manual_entry)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    def _submit_manual_entry(self, event):
        try:
            val = float(self.temp_entry.get())
            if self.min_val <= val <= self.max_val:
                self.variable.set(val)
                if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        except: pass
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None

@WidgetRegistry.register("_Fader", "_SmartFader", "_CustomFader")
class BuilderFaderCreator:
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating a Fader widget.
        Replaces the old instance-based make_fader.
        """
        if LOCAL_DEBUG: logger.trace(f"🔬 Entering BuilderFaderCreator.make with config: {config_data}")
        path = config_data.get("path")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")

        val_default = float(config_data.get("value_default", 75.0))
        fader_value_var = tk.DoubleVar(value=val_default)

        frame = None
        def on_drag_or_click_callback(event):
            canvas = event.widget
            height = float(canvas.winfo_height())
            if height <= 1: return
            norm_y_inverted = (event.y - 25) / (height - 45)
            norm_y_inverted = max(0.0, min(1.0, norm_y_inverted))
            norm_pos = 1.0 - norm_y_inverted
            log_norm = max(0.0000001, norm_pos) ** frame.log_exponent if frame.log_exponent != 1.0 else norm_pos
            current_value = frame.min_val + log_norm * (frame.max_val - frame.min_val)
            fader_value_var.set(current_value)
            if state_mirror_engine: state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        frame = CustomFaderFrame(parent_widget, fader_value_var, config_data, path, state_mirror_engine, on_drag_or_click_callback)

        try:
            l_cfg = config_data.get("layout", {})
            width = float(config_data.get("width", l_cfg.get("width", 100)))
            height = float(config_data.get("height", l_cfg.get("height", 250)))

            canvas = tk.Canvas(frame, width=int(width), height=int(height), highlightthickness=0, bd=0, relief="flat", bg=frame.bg_color)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            TransparencyManager.apply_transparency(frame, canvas, config_data, builder_instance)

            fader_state = {"_resize_timer": None}
            visual_props = {"secondary": frame.fader_track_color}

            def _update_fader_pos(*args):
                if not canvas.winfo_exists(): return
                w, h = float(canvas.winfo_width()), float(canvas.winfo_height())
                if w <= 1: w, h = width, height
                BuilderFaderCreator._sync_fader_cap_position(frame, canvas, w, h, fader_value_var.get())

            def _schedule_full_redraw(event=None):
                if fader_state["_resize_timer"]: canvas.after_cancel(fader_state["_resize_timer"])
                curr_w, curr_h = float(canvas.winfo_width()), float(canvas.winfo_height())
                if curr_w <= 1: curr_w, curr_h = width, height
                fader_state["_resize_timer"] = canvas.after(100, lambda: BuilderFaderCreator._draw_fader(frame, canvas, curr_w, curr_h, fader_value_var.get(), visual_props["secondary"]))

            frame._draw = _schedule_full_redraw
            fader_value_var.trace_add("write", _update_fader_pos)

            def on_mousewheel(event):
                current_val = fader_value_var.get()
                val_range = frame.max_val - frame.min_val
                step = val_range * 0.05
                delta = 1 if (event.num == 4 or event.delta > 0) else -1
                if sys.platform == "linux" and event.num == 5: delta = -1
                new_val = max(frame.min_val, min(frame.max_val, current_val + (delta * step)))
                frame.is_sliding = True
                fader_value_var.set(new_val)
                if state_mirror_engine: state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                canvas.after(500, lambda: setattr(frame, 'is_sliding', False) or _update_fader_pos())

            def _update_hover_state(hovering):
                frame.is_hovered = hovering
                if canvas.find_withtag("track_slot"):
                    col = frame.track_hover_color if hovering else "#050505"
                    canvas.itemconfig("track_slot", fill=col)

            canvas.bind("<Enter>", lambda e: _update_hover_state(True))
            canvas.bind("<Leave>", lambda e: _update_hover_state(False))
            canvas.bind("<MouseWheel>", on_mousewheel)
            canvas.bind("<Button-4>", on_mousewheel)
            canvas.bind("<Button-5>", on_mousewheel)

            def _stop_sliding_and_broadcast(e):
                # ⚡ RELEASE SEQUENCE
                if state_mirror_engine: state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                setattr(frame, 'is_sliding', False)
                setattr(frame, 'is_locked', False)
                _update_fader_pos()

            canvas.bind("<Button-1>", lambda e: setattr(frame, 'is_sliding', True) or setattr(frame, 'is_locked', True) or frame.command(e))
            canvas.bind("<B1-Motion>", frame.command)
            canvas.bind("<ButtonRelease-1>", _stop_sliding_and_broadcast)
            canvas.bind("<Button-2>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)
            canvas.bind("<Configure>", _schedule_full_redraw)

            if path and state_mirror_engine:
                # ⚡ HARDENED RANGE: Explicitly pass min/max to prevent clamping to 0.0
                reg_config = {**config_data, "value_min": frame.min_val, "value_max": frame.max_val}
                topic = state_mirror_engine.register_widget(path, fader_value_var, base_mqtt_topic_from_path, reg_config, instance=frame)
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            canvas.after(50, lambda: BuilderFaderCreator._draw_fader(frame, canvas, width, height, fader_value_var.get(), visual_props["secondary"]))
            if LOCAL_DEBUG: logger.success(f"✅ SUCCESS! The fader '{frame.label_text}' has materialized!")
            return frame
        except Exception as e:
            logger.exception("🎚️❌ Error creating custom fader")
            return None

    def make_fader(self, parent_widget, config_data, context=None, **kwargs):
        # Backward compatibility for mixin usage
        return BuilderFaderCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)

    @staticmethod
    def _sync_fader_cap_position(frame_instance, canvas, width, height, value):
        if not canvas.find_withtag("fader_cap"): return
        scale = float(frame_instance.fader_cap_scale)
        cap_h = int((float(frame_instance.cap_height_override) if frame_instance.cap_height_override else 50.0) * scale)
        padding = cap_h / 2.0
        top_res, bot_res = 25.0, 20.0
        f_h = float(height) - top_res - bot_res - (2.0 * padding)
        norm = (value - frame_instance.min_val) / (frame_instance.max_val - frame_instance.min_val) if (frame_instance.max_val - frame_instance.min_val) != 0 else 0
        disp_norm = max(0.0, min(1.0, norm)) ** (1.0 / frame_instance.log_exponent) if frame_instance.log_exponent != 1.0 else norm
        hy = f_h * (1.0 - disp_norm) + top_res + padding
        cx = float(width) / 2.0
        canvas.coords("fader_cap", cx, hy)
        if frame_instance.is_sliding:
            txt = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            canvas.itemconfig("floating_val", text=txt, state="normal")
            canvas.coords("floating_val", cx, hy - 10)
        else: canvas.itemconfig("floating_val", state="hidden")
        if frame_instance.show_value:
            val_str = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            if frame_instance.show_units and frame_instance.unit_text:
                val_str = f"{val_str} {frame_instance.unit_text}" if frame_instance.unit_position == "right" else f"{frame_instance.unit_text} {val_str}"
            canvas.itemconfig("static_readout", text=val_str)

    @staticmethod
    def _draw_fader(frame_instance, canvas, width, height, value, track_color=None):
        if not canvas.winfo_exists(): return
        width, height = float(width), float(height)
        if width <= 1 or height <= 1: return
        
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in canvas.find_all():
            tags = canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                canvas.delete(item)
        
        # 0. Draw Industrial Background (Fallback if slice doesn't exist)
        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
            canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
        cx = width / 2.0
        t_col = track_color if track_color else frame_instance.fader_track_color
        scale = float(frame_instance.fader_cap_scale)
        cap_w = int((float(frame_instance.cap_width_override) if frame_instance.cap_width_override else 40.0) * scale)
        cap_h = int((float(frame_instance.cap_height_override) if frame_instance.cap_height_override else 50.0) * scale)
        padding = cap_h / 2.0
        top_res, bot_res = 25.0, 20.0
        u_h = height - top_res - bot_res
        if frame_instance.label_text:
            canvas.create_text(cx, 12, text=frame_instance.label_text, fill=frame_instance.label_color, font=("Helvetica", 10, "bold"), anchor="n", tags="static")
        TrackDrawer.draw(canvas, frame_instance, cx, top_res + padding, height - bot_res, 10, hover_color=frame_instance.track_hover_color if frame_instance.is_hovered else None)
        f_h = u_h - (2.0 * padding)
        ScaleDrawer.draw(canvas, frame_instance, width, height - bot_res, cx, f_h, top_res + padding, width * frame_instance.tick_size, 10, cap_width=cap_w)
        norm = (value - frame_instance.min_val) / (frame_instance.max_val - frame_instance.min_val) if (frame_instance.max_val - frame_instance.min_val) != 0 else 0
        disp_norm = max(0.0, min(1.0, norm)) ** (1.0 / frame_instance.log_exponent) if frame_instance.log_exponent != 1.0 else norm
        hy = f_h * (1.0 - disp_norm) + top_res + padding
        cap_img = CapDrawer.get_3d_fader_cap(cap_w, cap_h, frame_instance.cap_color, t_col, highlight_color=frame_instance.cap_highlight_color)
        canvas.create_image(cx, hy, image=cap_img, tags="fader_cap")
        canvas.cap_img = cap_img 
        canvas.create_text(cx, hy - 10, text="", fill="#FFFFFF", font=("Helvetica", 7, "bold"), tags="floating_val", anchor="s", state="hidden")
        if frame_instance.show_value:
            val_str = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            if frame_instance.show_units and frame_instance.unit_text:
                val_str = f"{val_str} {frame_instance.unit_text}" if frame_instance.unit_position == "right" else f"{frame_instance.unit_text} {val_str}"
            canvas.create_text(cx, height - 10, text=val_str, fill=frame_instance.value_highlight_color, font=("Helvetica", 8), anchor="s", tags="static_readout")
