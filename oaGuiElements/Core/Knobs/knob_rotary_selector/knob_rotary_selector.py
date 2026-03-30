# knob_rotary_selector/knob_rotary_selector.py
# Author: Anthony Peter Kuzub
# Version: 20260223.Modernized.1
#
# Description: A specialized knob for multi-position rotary switching.

import tkinter as tk
import math

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaGuiElements.Core.Knobs.knob.knob import CustomKnobFrame
from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# Core Modules for Knob Rendering
from ..knob.Core.knob_renderer import _draw_body, _draw_pointer
from ..knob.Core.knob_config import extract_knob_config
from ..knob.Core.knob_state import create_knob_state

class RotarySelectorSwitch(CustomKnobFrame):
    """
    A specialized frame for a multi-position selector switch.
    Inherits from CustomKnobFrame to leverage common event handling and state.
    """
    def __init__(self, parent, variable, positions, continuous=False, path=None, state_mirror_engine=None, config=None, state=None, label_text="", **kwargs):
        self.positions = positions
        self.continuous = continuous
        self.num_positions = len(positions)
        
        super().__init__(
            parent, variable, 
            config, state,
            path, 
            state_mirror_engine=state_mirror_engine, 
            label_text=label_text,
            **kwargs
        )

    def _draw_visuals(self):
        """Override base visuals with selector-specific rendering."""
        if not self.canvas.winfo_exists(): return
        
        idx = int(round(self.variable.get()))
        idx = idx % self.num_positions if self.continuous else max(0, min(self.num_positions - 1, idx))
        
        sel_text = str(self.positions[idx])
        
        colors = {
            "fg": self.widget_config.get("fg_color", self.theme_colors.get("fg", "white")),
            "accent": self.widget_config.get("accent_color", self.theme_colors.get("accent", "cyan")),
            "indicator": self.widget_config.get("indicator_color", "yellow"),
            "secondary": self.widget_config.get("secondary_color", self.theme_colors.get("secondary", "gray"))
        }
        
        options = {
            "shape": self.widget_config.get("shape", "circle"),
            "pointer_style": self.widget_config.get("pointer_style", "line"),
            "knob_style": self.widget_config.get("knob_style", "standard"),
            "no_center": self.widget_config.get("no_center", False),
            "continuous": self.continuous,
            "main_label": self.label_text,
            "selection_text": sel_text,
            "show_label": self.widget_config.get("show_label", True)
        }
        
        self._draw_selector(self.canvas, self.winfo_width(), self.winfo_height(), idx, self.positions, colors, options)

    def _draw_selector(self, canvas, width, height, current_idx, positions, colors, options):
        """Internal drawing pipeline for the selector switch."""
        self._prepare_canvas(canvas)
        
        layout = self._calc_layout(width, height, options)
        angles = self._calc_angles(len(positions), options.get("continuous", False))
        
        self._draw_track(canvas, layout, angles, colors['secondary'], options.get("continuous", False))
        self._draw_ticks_and_labels(canvas, layout, angles, current_idx, positions, colors)
        self._draw_knob_elements(canvas, layout, angles, current_idx, colors, options)
        self._draw_text_overlays(canvas, width, height, colors, options)

    def _prepare_canvas(self, canvas):
        """Preserve industrial transparency slice while clearing other elements."""
        for item in canvas.find_all():
            if "panel_bg_slice" not in canvas.gettags(item):
                canvas.delete(item)
        
        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
            canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

    def _calc_layout(self, width, height, options):
        """Calculate center points and usable radius."""
        cx, cy = width / 2, height / 2
        top_res = 20 if options.get("show_label") and options.get("main_label") else 0
        bottom_res = 20
        usable_h = height - top_res - bottom_res
        adj_cy = cy + (top_res - bottom_res) / 2
        radius = min(width, usable_h) / 2 - 25
        return {'cx': cx, 'cy': cy, 'adj_cy': adj_cy, 'radius': radius}

    def _calc_angles(self, num_pos, continuous):
        """Determine angular start, step, and total span."""
        start_angle, total_span = (90, 360) if continuous else (240, 300)
        angle_step = total_span / (num_pos if continuous else max(1, num_pos - 1))
        return {'start': start_angle, 'step': angle_step, 'span': total_span}

    def _draw_track(self, canvas, layout, angles, color, continuous):
        """Draw the circular or arc track."""
        cx, adj_cy, radius = layout['cx'], layout['adj_cy'], layout['radius']
        if continuous: 
            canvas.create_oval(cx - radius, adj_cy - radius, cx + radius, adj_cy + radius, outline=color, width=2)
        else: 
            canvas.create_arc(cx - radius, adj_cy - radius, cx + radius, adj_cy + radius, 
                               start=angles['start'], extent=-angles['span'], style=tk.ARC, outline=color, width=2)

    def _draw_ticks_and_labels(self, canvas, layout, angles, current_idx, positions, colors):
        """Draw position ticks and labels around the track."""
        cx, adj_cy, radius = layout['cx'], layout['adj_cy'], layout['radius']
        for i, pos_text in enumerate(positions):
            angle_deg = angles['start'] - (i * angles['step'])
            angle_rad = math.radians(angle_deg)
            ts_x, ts_y = cx + (radius + 2) * math.cos(angle_rad), adj_cy - (radius + 2) * math.sin(angle_rad)
            te_x, te_y = cx + (radius + 10) * math.cos(angle_rad), adj_cy - (radius + 10) * math.sin(angle_rad)
            tl_x, tl_y = cx + (radius + 24) * math.cos(angle_rad), adj_cy - (radius + 24) * math.sin(angle_rad)
            
            canvas.create_line(ts_x, ts_y, te_x, te_y, fill=colors['secondary'], width=1)
            canvas.create_text(
                tl_x, tl_y, text=str(pos_text), 
                fill=colors['indicator'] if i == current_idx else colors['fg'], 
                font=("Helvetica", 8, "bold" if i == current_idx else "normal"), 
                tags="industrial_text"
            )

    def _draw_knob_elements(self, canvas, layout, angles, current_idx, colors, options):
        """Draw the physical knob body and pointer."""
        cx, adj_cy, radius = layout['cx'], layout['adj_cy'], layout['radius']
        p_angle = angles['start'] - (current_idx * angles['step'])
        _draw_body(canvas, cx, adj_cy, radius - 5, options.get("shape", "circle"), colors['secondary'], 1, 
                   rotation_angle=p_angle, outline_thickness=1, fill_color="", teeth=8)
        _draw_pointer(canvas, cx, adj_cy, radius - 5, 4, p_angle, options.get("pointer_style", "line"), 
                      colors['indicator'], length=radius+14, offset=0, no_center=options.get("no_center", False))

    def _draw_text_overlays(self, canvas, width, height, colors, options):
        """Draw the main title and selection value text."""
        cx = width / 2
        if options.get("show_label") and options.get("main_label"):
            canvas.create_text(cx, 10, text=options.get("main_label"), fill=colors['fg'], 
                               font=("Helvetica", 9, "bold"), anchor="n", tags="industrial_text")
        if options.get("selection_text"):
            canvas.create_text(cx, height - 10, text=options.get("selection_text"), fill=colors['indicator'], 
                               font=("Helvetica", 9, "bold"), anchor="s", tags="industrial_text")

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
        
        # Value Handling
        val_def = config_data.get("value_default", 0)
        if isinstance(val_def, str) and val_def in positions: 
            val_def = positions.index(val_def)
            
        knob_value_var = tk.DoubleVar(master=parent_widget, value=float(val_def))
        if LOCAL_DEBUG: builder_logger.debug(f"🔋🔢✨ [STATE] Initial position value: {val_def}")
        
        # 1. Container frame background
        try:
            p_bg = parent_widget.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except:
            p_bg = "#2b2b2b"

        # ⚡ SRP COMPLIANCE: Use extraction logic from CustomKnob's core
        knob_config = extract_knob_config(config_data)
        # Override min/max for selector behavior
        knob_config["min"] = 0
        knob_config["max"] = num_pos - 1
        knob_config["reff_point"] = 0
        
        knob_state = create_knob_state(knob_config)

        if LOCAL_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating RotarySelectorSwitch for '{label}'")
        frame = RotarySelectorSwitch(
            parent_widget, knob_value_var, positions, continuous, path,
            state_mirror_engine=state_mirror_engine,
            config=knob_config, state=knob_state,
            label_text=label,
            width=width, height=height,
            bg=p_bg
        )

        # ⚡ INDUSTRIAL TRANSPARENCY: Apply via Manager
        if hasattr(builder_instance, '_apply_transparency'):
            if LOCAL_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to rotary selector '{label}'")
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, builder_instance)
            TransparencyManager.apply_transparency(frame, frame, config_data, builder_instance)

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

        if LOCAL_DEBUG: builder_logger.success(f"✅🆗🎛️ [SUCCESS] The rotary selector switch '{label}' has materialized!")
        return frame
