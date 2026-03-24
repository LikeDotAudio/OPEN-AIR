# meter_knob_with_vu_meter/meter_knob_with_vu_meter.py
# Author: Anthony Peter Kuzub
# Version: 20260115.Composite.1
#
# Description: meter_knob_with_vu_meter/VU_Meter_Knob.py

import tkinter as tk
from tkinter import ttk
import copy
import math

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

@WidgetRegistry.register("_VUMeterKnob")
class BuilderMeterKnobWithVuMeterCreator(TransparencyMixin):
    """
    Mixin for creating a composite VU Meter + Knob widget.
    Requires BuilderMeterNeedleCreator and BuilderKnobCreator to be present in the host class.
    """

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Static factory method for the registry."""
        return BuilderMeterKnobWithVuMeterCreator().make_meter_knob_with_vu_meter(
            parent_widget, config_data, context=context, **kwargs
        )

    def make_meter_knob_with_vu_meter(self, parent_widget, config_data, context=None, **kwargs):
        if LOCAL_DEBUG: logger.trace(f"🔬 Entering make_meter_knob_with_vu_meter with config: {config_data}")
        """
        Creates a Needle VU Meter with a Knob at its pivot point.
        """
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
        else:
            state_mirror_engine = getattr(self, "state_mirror_engine", None)
            subscriber_router = getattr(self, "subscriber_router", None)
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            app_instance = kwargs.get("app_instance")

        try:
            # 1. Split Configuration
            vu_config = copy.deepcopy(config_data)
            knob_config = copy.deepcopy(config_data)

            # Process knob-specific keys
            for key, value in config_data.items():
                if key.startswith("knob_"):
                    new_key = key[5:]
                    knob_config[new_key] = value
            
            # Force disable label on Knob (redundant if on top of VU)
            if "knob_label_active" not in config_data:
                knob_config["show_label"] = False

            if LOCAL_DEBUG: logger.debug(f"🛠️ VUMeterKnob: Building for '{vu_config.get('label_active')}'.")

            # 2. Create VU Meter (This now returns a Canvas or transparent Frame)
            from oaGuiElements.Core.metering.meter_needle.meter_needle import BuilderMeterNeedleCreator
            vu_widget = BuilderMeterNeedleCreator.make(parent_widget, vu_config, context=context, builder_instance=builder_instance, **kwargs)
            if not vu_widget:
                return None

            # 3. Locate Canvas
            canvas = vu_widget if isinstance(vu_widget, tk.Canvas) else None
            if not canvas:
                for child in vu_widget.winfo_children():
                    if isinstance(child, tk.Canvas):
                        canvas = child
                        break
            
            if not canvas:
                return vu_widget

            # --- DYNAMIC CENTERING ---
            # Retrieve dynamic offsets stored by the NeedleVUMeter builder
            center_x = getattr(vu_widget, "pivot_offset_x", 0)
            center_y = getattr(vu_widget, "pivot_offset_y", 0)
            
            layout_config = vu_config.get("layout", {})
            size = int(layout_config.get("width", vu_config.get("size", 150)))
            
            if center_x == 0 or center_y == 0:
                center_x = size / 2
                center_y = size / 2 + 10
            
            # 4. Create Knob
            if "width" not in knob_config and "knob_width" not in config_data:
                 knob_config["width"] = 40
            if "height" not in knob_config and "knob_height" not in config_data:
                 knob_config["height"] = 40
                 
            # Knob is embedded in the VU canvas
            from oaGuiElements.Core.utils.knob.knob import BuilderKnobCreator
            knob_widget = BuilderKnobCreator.make(canvas, knob_config, context=context, builder_instance=builder_instance, **kwargs)
            
            if knob_widget:
                # 5. Check for Clipping and Resize Canvas if needed
                knob_height = int(knob_config.get("height", 40))
                knob_half_height = knob_height / 2
                
                # Check bottom overlap
                meter_viewable_angle = float(vu_config.get("Meter_viewable_angle", 90.0))
                half_angle = meter_viewable_angle / 2.0
                start_angle = 90 + half_angle
                end_angle = 90 - half_angle
                main_arc_radius = (size - 20) / 2
                
                angles_to_check = [start_angle, end_angle]
                if start_angle >= 270 or end_angle <= -90:
                    angles_to_check.append(270)
                
                min_sin = min([math.sin(math.radians(a)) for a in angles_to_check])
                arc_depth_below_pivot = -min_sin * main_arc_radius if min_sin < 0 else 0
                required_below_pivot = max(knob_half_height, arc_depth_below_pivot)
                
                current_h = int(canvas.cget("height"))
                if center_y + required_below_pivot > current_h:
                    new_h = int(center_y + required_below_pivot + 10)
                    canvas.configure(height=new_h)

                # 6. Position Knob
                canvas.create_window(center_x, center_y, window=knob_widget, anchor="center", tags="knob_composite")
                canvas.lift("knob_composite") 
                
                # Link redraw hooks
                old_draw = getattr(vu_widget, "_draw", lambda: None)
                def composite_draw():
                    old_draw()
                    if hasattr(knob_widget, "_draw"): knob_widget._draw()
                
                vu_widget._draw = composite_draw
                vu_widget.render = composite_draw

            return vu_widget

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ VUMeterKnob creation failed")
            return None
