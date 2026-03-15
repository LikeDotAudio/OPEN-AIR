# workers/builder/knob_rotary_selector/knob_rotary_selector.py
#
# A specialized knob for multi-position rotary switching.
# Supports Industrial Transparency and procedural rendering.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260223.Modernized.1

import tkinter as tk
import math

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from workers.builder.knob.knob import CustomKnobFrame
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

# Core Modules for Knob Rendering
from ..knob.core.knob_renderer import _draw_body, _draw_pointer

class RotarySelectorSwitch(CustomKnobFrame):
    """
    A specialized frame for a multi-position selector switch.
    Inherits from CustomKnobFrame to leverage common event handling and state.
    """
    def __init__(self, parent, variable, positions, continuous=False, path=None, state_mirror_engine=None, *args, **kwargs):
        self.positions = positions
        self.continuous = continuous
        self.num_positions = len(positions)
        
        # Calculate min/max for the underlying DoubleVar
        min_val = 0
        max_val = self.num_positions - 1
        
        super().__init__(
            parent, variable=variable, 
            min_val=min_val, max_val=max_val, 
            reff_point=0, path=path, 
            state_mirror_engine=state_mirror_engine, 
            command=None, *args, **kwargs
        )

    def _draw_selector(self, canvas, width, height, current_idx, positions, fg_color, accent_color, indicator_color, secondary, 
                       shape="circle", pointer_style="line", knob_style="standard", no_center=False, continuous=False,
                       main_label=None, selection_text=None, show_label=True):
        """Internal drawing pipeline for the selector switch."""
        
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in canvas.find_all():
            tags = canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                canvas.delete(item)
        
        # 0. Draw Industrial Background (Fallback if slice doesn't exist)
        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
            canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
        cx, cy, num_pos = width / 2, height / 2, len(positions)
        
        # Reserves for labels
        top_reserve = 20 if show_label and main_label else 0
        bottom_reserve = 20 # Always some space for the selection label
        
        usable_h = height - top_reserve - bottom_reserve
        adj_cy = cy + (top_reserve - bottom_reserve) / 2
        
        start_angle, total_span = (90, 360) if continuous else (240, 300)
        angle_step = total_span / (num_pos if continuous else max(1, num_pos - 1))
        
        radius = min(width, usable_h) / 2 - 25
        
        # 1. Draw Track
        if continuous: 
            canvas.create_oval(cx - radius, adj_cy - radius, cx + radius, adj_cy + radius, outline=secondary, width=2)
        else: 
            canvas.create_arc(cx - radius, adj_cy - radius, cx + radius, adj_cy + radius, start=start_angle, extent=-total_span, style=tk.ARC, outline=secondary, width=2)

        # 2. Draw Position Ticks and Labels
        for i, pos_text in enumerate(positions):
            angle_deg = start_angle - (i * angle_step)
            angle_rad = math.radians(angle_deg)
            ts_x, ts_y = cx + (radius + 2) * math.cos(angle_rad), adj_cy - (radius + 2) * math.sin(angle_rad)
            te_x, te_y = cx + (radius + 10) * math.cos(angle_rad), adj_cy - (radius + 10) * math.sin(angle_rad)
            tl_x, tl_y = cx + (radius + 24) * math.cos(angle_rad), adj_cy - (radius + 24) * math.sin(angle_rad)
            
            canvas.create_line(ts_x, ts_y, te_x, te_y, fill=secondary, width=1)
            canvas.create_text(
                tl_x, tl_y, text=str(pos_text), 
                fill=indicator_color if i == current_idx else fg_color, 
                font=("Helvetica", 8, "bold" if i == current_idx else "normal"), 
                tags="industrial_text"
            )

        # 3. Draw Knob Body and Pointer
        p_angle = start_angle - (current_idx * angle_step)
        _draw_body(canvas, cx, adj_cy, radius - 5, shape, secondary, 1, rotation_angle=p_angle, outline_thickness=1, fill_color="", teeth=8)
        _draw_pointer(canvas, cx, adj_cy, radius - 5, 4, p_angle, pointer_style, indicator_color, length=radius+14, offset=0, no_center=no_center)

        # 4. Draw Main Label (Title)
        if show_label and main_label:
            canvas.create_text(cx, 10, text=main_label, fill=fg_color, font=("Helvetica", 9, "bold"), anchor="n", tags="industrial_text")

        # 5. Draw Selection Label (Current Value)
        if selection_text:
            canvas.create_text(cx, height - 10, text=selection_text, fill=indicator_color, font=("Helvetica", 9, "bold"), anchor="s", tags="industrial_text")

@WidgetRegistry.register("SelectorSwitch", "_SelectorSwitch")
class BuilderKnobRotarySelectorCreator:
    """Factory for creating Rotary Selector Switch widgets."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Static factory method for the registry."""
        return BuilderKnobRotarySelectorCreator.make_knob_rotary_selector(
            parent_widget, config_data, context=context, **kwargs
        )

    @staticmethod
    def make_knob_rotary_selector(parent_widget, config_data, context=None, **kwargs):
        """Main entry point for creating a rotary selector."""
        if LOCAL_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎛️ [BUILDER] Entering make_knob_rotary_selector")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        label = config_data.get("label_active")
        path = config_data.get("path")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if LOCAL_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if LOCAL_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            if LOCAL_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.")

        positions = config_data.get("positions", ["OFF", "ON"])
        continuous = config_data.get("continuous", False)
        num_pos = len(positions)
        if LOCAL_DEBUG: builder_logger.debug(f"🎛️🔀🔢 [STATE] Positions: {positions}, Continuous: {continuous}")
        
        width = config_data.get("width", 120)
        height = config_data.get("height", 140)
        if LOCAL_DEBUG: builder_logger.debug(f"📐📏🔳 [LAYOUT] Dimensions: {width}x{height}")
        
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")
        indicator_color = config_data.get("indicator_color", accent_color)
        
        # Value Handling
        val_def = config_data.get("value_default", 0)
        if isinstance(val_def, str) and val_def in positions: 
            val_def = positions.index(val_def)
            
        knob_value_var = tk.DoubleVar(value=float(val_def))
        if LOCAL_DEBUG: builder_logger.debug(f"🔋🔢✨ [STATE] Initial position value: {val_def}")
        
        drag_state = {"start_y": None, "start_value": None}

        # 1. Container frame
        try:
            p_bg = parent_widget.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except:
            p_bg = "#2b2b2b"

        if LOCAL_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating RotarySelectorSwitch for '{label}'")
        frame = RotarySelectorSwitch(
            parent_widget, variable=knob_value_var, 
            positions=positions, continuous=continuous, 
            path=path, state_mirror_engine=state_mirror_engine,
            width=width, height=height,
            bg=p_bg
        )
        frame.pack_propagate(False)

        # 2. Canvas
        if LOCAL_DEBUG: builder_logger.trace(f"🏗️🪟🖼️ [CONSTRUCT] Creating drawing canvas for rotary selector.")
        canvas = tk.Canvas(frame, width=width, height=height, highlightthickness=0, bd=0, relief="flat", bg=p_bg)
        canvas.pack(expand=True, fill=tk.BOTH)

        # ⚡ INDUSTRIAL TRANSPARENCY: Apply via Manager
        if hasattr(builder_instance, '_apply_transparency'):
            if LOCAL_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to rotary selector '{label}'")
            TransparencyManager.apply_transparency(frame, canvas, config_data, builder_instance)
            TransparencyManager.apply_transparency(frame, frame, config_data, builder_instance)

        def update_visuals(*args):
            if not canvas.winfo_exists(): return
            
            idx = int(round(knob_value_var.get()))
            idx = idx % num_pos if continuous else max(0, min(num_pos - 1, idx))
            
            sel_text = str(positions[idx])
            if LOCAL_DEBUG: builder_logger.trace(f"🔄✨🎨 [REDRAW] Updating rotary selector '{label}' visuals to index {idx} ('{sel_text}')")
            
            frame._draw_selector(
                canvas, width, height, idx, positions, 
                fg_color, accent_color, indicator_color, secondary_color, 
                shape=config_data.get("shape", "circle"), 
                pointer_style=config_data.get("pointer_style", "line"), 
                knob_style=config_data.get("knob_style", "standard"), 
                no_center=config_data.get("no_center", False), 
                continuous=continuous,
                main_label=label,
                selection_text=sel_text,
                show_label=config_data.get("show_label", True)
            )

        def sync_bg():
            update_visuals() 

        frame._draw = sync_bg
        frame.render = sync_bg

        # 3. Bindings
        def on_knob_drag(event):
            if drag_state["start_y"] is None: return
            new_val = drag_state["start_value"] + (drag_state["start_y"] - event.y) / 40.0
            knob_value_var.set(new_val % num_pos if continuous else max(0.0, min(num_pos - 1, new_val)))

        def on_knob_release(event):
            snapped = round(knob_value_var.get())
            final_idx = snapped % num_pos if continuous else max(0, min(num_pos - 1, snapped))
            if LOCAL_DEBUG: builder_logger.info(f"🖱️🔙🎛️ [INPUT] Rotary selector '{label}' released at position {final_idx}")
            knob_value_var.set(float(final_idx))
            drag_state.update({"start_y": None, "start_value": None})
            if path and state_mirror_engine: 
                if LOCAL_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Broadcasting rotary selector change for '{path}'")
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        def on_mousewheel(event):
            delta = 1 if (event.num == 4 or event.delta > 0) else -1
            new_val = round(knob_value_var.get()) + delta
            final_idx = new_val % num_pos if continuous else max(0, min(num_pos-1, new_val))
            if LOCAL_DEBUG: builder_logger.info(f"🖱️🔄🎛️ [INPUT] Rotary selector '{label}' wheel adjustment to {final_idx}")
            knob_value_var.set(float(final_idx))
            if path and state_mirror_engine: 
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        if LOCAL_DEBUG: builder_logger.trace(f"🖱️👆🔗 [EVENTS] Binding input protocols for rotary selector '{label}'")
        canvas.bind("<Button-1>", lambda e: setattr(frame, 'is_locked', True) or drag_state.update({"start_y": e.y, "start_value": knob_value_var.get()}))
        canvas.bind("<B1-Motion>", on_knob_drag)
        canvas.bind("<ButtonRelease-1>", lambda e: on_knob_release(e) or (state_mirror_engine.broadcast_gui_change_to_mqtt(path) if path and state_mirror_engine else None) or setattr(frame, 'is_locked', False))
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)
        canvas.bind("<Button-5>", on_mousewheel)

        knob_value_var.trace_add("write", update_visuals)
        
        # 4. MQTT Registration
        if path and state_mirror_engine:
            if LOCAL_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering rotary selector at path '{path}'")
            # ⚡ LOCK REGISTRATION: Pass 'frame' as instance
            topic = state_mirror_engine.register_widget(path, knob_value_var, base_mqtt_topic_from_path, config_data, instance=frame)
            if subscriber_router and topic:
                if LOCAL_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if LOCAL_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'")
            state_mirror_engine.initialize_widget_state(path)

        # Initial Render
        update_visuals()
        
        if LOCAL_DEBUG: builder_logger.success(f"✅🆗🎛️ [SUCCESS] The rotary selector switch '{label}' has materialized!")
        return frame
