# builder_composite/VU_Meter_Knob.py
#
# A composite widget combining a Needle VU Meter and a Rotary Knob.
# The Knob is positioned at the pivot point of the VU Meter.
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
# Version 20260115.Composite.1

import tkinter as tk
from tkinter import ttk
from workers.logger.logger import debug_logger
import copy
import math

class VUMeterKnobCreatorMixin:
    """
    Mixin for creating a composite VU Meter + Knob widget.
    Requires NeedleVUMeterCreatorMixin and KnobCreatorMixin to be present in the host class.
    """

    def _create_vu_meter_knob(self, parent_widget, config_data, **kwargs):
        """
        Creates a Needle VU Meter with a Knob at its pivot point.
        
        Config Keys:
        - All standard VU Meter keys (min, max, path, etc.) apply to the VU Meter.
        - Keys prefixed with 'knob_' (e.g., knob_min, knob_max, knob_path) are passed to the Knob
          after stripping the prefix.
        - 'knob_width' and 'knob_height' control the knob size.
        """
        try:
            # 1. Split Configuration
            vu_config = copy.deepcopy(config_data)
            knob_config = copy.deepcopy(config_data)

            # Process knob-specific keys
            keys_to_remove_from_knob = []
            for key, value in config_data.items():
                if key.startswith("knob_"):
                    # Strip prefix and add to knob_config
                    new_key = key[5:] # remove 'knob_'
                    knob_config[new_key] = value
                
            # Ensure Knob doesn't inherit conflicting VU params if not explicitly set
            # For example, if 'min' is set for VU, we don't want Knob to use it unless 'knob_min' was not provided.
            # However, my logic above essentially overwrites 'min' with 'knob_min' if present.
            # But if 'knob_min' is NOT present, 'min' (VU's min) remains in knob_config.
            # This might be intended (shared range) or not.
            # Safest is to clean knob_config of standard VU keys if they shouldn't share.
            # But "combine all options" suggests flexibility.
            # Let's trust the 'knob_' prefix override.
            
            # Explicitly handle 'path' collision
            if "knob_path" in config_data:
                knob_config["path"] = config_data["knob_path"]
            elif "path" in knob_config and "knob_path" not in config_data:
                # If no specific knob path, maybe remove the VU path to avoid conflict?
                # Or assume they share the path (unlikely for VU and Knob).
                # Let's remove 'path' from knob_config if 'knob_path' wasn't provided,
                # unless the user intends them to share (which would be weird: value vs setting).
                # We'll leave it, but warn if debug.
                pass

            # Force disable label on Knob (usually redundant if on top of VU)
            if "knob_label_active" not in config_data:
                knob_config["show_label"] = False

            debug_logger(message=f"🛠️ VUMeterKnob: Building for '{vu_config.get('label_active')}'. Knob Config keys: {list(knob_config.keys())}")

            # 2. Create VU Meter
            # We use the host's method.
            vu_frame = self._create_needle_vu_meter(parent_widget, vu_config, **kwargs)
            if not vu_frame:
                debug_logger(message="❌ VUMeterKnob: VU Frame creation failed.")
                return None
            debug_logger(message="✅ VUMeterKnob: VU Frame created.")

            # 3. Locate Canvas and Pivot
            canvas = None
            children = vu_frame.winfo_children()
            debug_logger(message=f"🔍 VUMeterKnob: VU Frame children: {children}")
            
            for child in children:
                if isinstance(child, tk.Canvas):
                    canvas = child
                    break
            
            if not canvas:
                debug_logger(message="❌ VUMeterKnob: Could not find Canvas in VU Meter frame.")
                return vu_frame # Return at least the VU meter
            debug_logger(message=f"✅ VUMeterKnob: Canvas found: {canvas}")

            # Calculate Pivot Position
            # Logic mirrored from _draw_needle_vu_meter
            # height = size / 2 + 20
            # center_x = width / 2
            # center_y = height - 10
            
            # Retrieve size from config or defaults used in VU Meter
            layout_config = vu_config.get("layout", {})
            size = int(layout_config.get("width", vu_config.get("size", 150)))
            
            # Recalculate center based on VU Meter logic
            width = size
            height = size / 2 + 20
            center_x = width / 2
            center_y = height - 10
            
            debug_logger(message=f"📍 VUMeterKnob: Target Center: ({center_x}, {center_y})")

            # 4. Create Knob
            # We parent it to the canvas initially? No, _create_knob expects a parent widget.
            # If we parent to 'canvas', it becomes a child window.
            # However, _create_knob returns a Frame (CustomKnobFrame).
            # We can place this Frame into the Canvas using create_window.
            
            # Adjust Knob Config for size if not provided
            if "width" not in knob_config and "knob_width" not in config_data:
                 knob_config["width"] = 40
            if "height" not in knob_config and "knob_height" not in config_data:
                 knob_config["height"] = 40
                 
            knob_frame = self._create_knob(canvas, knob_config, **kwargs)
            
            if knob_frame:
                # 5. Check for Clipping and Resize Canvas
                knob_height = int(knob_config.get("height", 40))
                pivot_y_from_bottom = 10  # Because center_y = height - 10
                knob_half_height = knob_height / 2
                
                # --- New: Arc Depth Check ---
                meter_viewable_angle = float(vu_config.get("Meter_viewable_angle", 90.0))
                half_angle = meter_viewable_angle / 2.0
                start_angle = 90 + half_angle
                end_angle = 90 - half_angle
                
                # Standard radius calculation from VU Meter
                main_arc_radius = (size - 20) / 2
                
                # Find minimum sine (lowest point in Tkinter's top-center 90-degree based coords)
                # Tkinter Y = cy - r * sin(angle)
                # To maximize Y (go down), we need minimum sin(angle).
                # We check endpoints and potentially the 270/-90 degree point if in range.
                
                angles_to_check = [start_angle, end_angle]
                # If range covers bottom (270 / -90), add it.
                # Since start/end are centered at 90, for 270 deg range is [-45, 225]. 270 is not reached.
                # For 360 deg range is [-90, 270]. 270 is reached.
                if start_angle >= 270 or end_angle <= -90:
                    angles_to_check.append(270)
                
                min_sin = min([math.sin(math.radians(a)) for a in angles_to_check])
                
                arc_depth_below_pivot = 0
                if min_sin < 0:
                    arc_depth_below_pivot = -min_sin * main_arc_radius
                
                required_below_pivot = max(knob_half_height, arc_depth_below_pivot)
                
                # If required space extends below the pivot more than the available 10px
                overflow = required_below_pivot - pivot_y_from_bottom
                
                if overflow > 0:
                    current_canvas_height = height # Calculated above as size / 2 + 20
                    new_canvas_height = int(current_canvas_height + overflow + 5) # +5 padding
                    canvas.configure(height=new_canvas_height)
                    debug_logger(message=f"📏 VUMeterKnob: Resized Canvas to {new_canvas_height} to fit Knob/Arc (depth: {arc_depth_below_pivot:.1f}).")

                # 6. Position Knob
                # create_window coordinates are for the anchor (default center)
                canvas.create_window(center_x, center_y, window=knob_frame, anchor="center", tags="knob_composite")
                debug_logger(message=f"✅ VUMeterKnob: Knob embedded at ({center_x}, {center_y}) with size {knob_config.get('width')}x{knob_config.get('height')}")
                
                # Double check Z-order
                canvas.lift("knob_composite") # Ensure it's on top of everything else
            else:
                 debug_logger(message="❌ VUMeterKnob: Failed to create internal Knob.")
            
            return vu_frame

        except Exception as e:
            debug_logger(message=f"❌ VUMeterKnob creation failed: {e}")
            return None
