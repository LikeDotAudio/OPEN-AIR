# Methods/invert_handler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from .base_handler import BaseHandler

class InvertHandler(BaseHandler):
    """
    Inverts a numerical value within a given range, or a boolean value.
    """
    def execute(self, value, splink=None, state=None, direction="FORWARD"):
        
        # Handle boolean inversion
        if isinstance(value, bool):
            return not value
            
        if isinstance(value, (int, float)):
            max_value = self.params.get("max_value", 1)
            min_value = self.params.get("min_value", 0)
            try:
                val_float = float(value)
                inverted_val = (max_value + min_value) - val_float
                
                # Return original type if possible
                if isinstance(value, int):
                    return int(round(inverted_val))
                return inverted_val
            except (ValueError, TypeError):
                return value # Pass through if not a number
                
        # Handle string booleans
        if isinstance(value, str):
            val_lower = value.lower()
            if val_lower in ["true", "on", "1"]:
                return "false"
            if val_lower in ["false", "off", "0"]:
                return "true"

        return value
