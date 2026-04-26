# Methods/scale_handler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from ..Constants.constants import Splinker_debug_enabled, splinker_logger
from .base_handler import BaseHandler


class ScaleHandler(BaseHandler):
    """
    Linearly scales a value from a source range to a destination range.
    Supports inverse scaling if direction is "REVERSE".
    """
    def execute(self, value, splink=None, state=None, direction="FORWARD"):
        s_min = self.params.get("source_min", 0)
        s_max = self.params.get("source_max", 100)
        d_min = self.params.get("dest_min", 0)
        d_max = self.params.get("dest_max", 255)

        try:
            val_float = float(value)

            if direction == "REVERSE":
                src_in_min, src_in_max = d_min, d_max
                dest_out_min, dest_out_max = s_min, s_max
            else:
                src_in_min, src_in_max = s_min, s_max
                dest_out_min, dest_out_max = d_min, d_max

            if Splinker_debug_enabled:
                splinker_logger.trace(f"⚖️ ScaleHandler ({direction}): In={val_float} | Range=[{src_in_min}..{src_in_max}] -> [{dest_out_min}..{dest_out_max}]")

            # 1. Clamp input to input range
            in_min, in_max = min(src_in_min, src_in_max), max(src_in_min, src_in_max)
            clamped_val = max(in_min, min(in_max, val_float))

            # 2. Linear Scaling
            input_span = src_in_max - src_in_min
            output_span = dest_out_max - dest_out_min

            if input_span == 0:
                return dest_out_min

            scaled_value = dest_out_min + (((clamped_val - src_in_min) / input_span) * output_span)

            # 3. Preservation of type (int if both dest limits are int)
            result = scaled_value
            if isinstance(dest_out_min, int) and isinstance(dest_out_max, int):
                result = int(round(scaled_value))

            if Splinker_debug_enabled:
                splinker_logger.trace(f"⚖️ ScaleHandler Result: {result}")

            return result

        except (ValueError, TypeError) as e:
            if Splinker_debug_enabled:
                splinker_logger.error(f"⚖️ ScaleHandler Error: {e}")
            return value
