# Methods/deadband_handler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from .base_handler import BaseHandler

class DeadbandHandler(BaseHandler):
    """
    Drops messages if the value change is within a certain threshold.
    Stateful: needs to remember the last value that was passed.
    """
    def execute(self, value, splink=None, state=None, direction="FORWARD"):
        threshold_percent = self.params.get("threshold_percent", 1)
        max_value = self.params.get("max_value", 100) # Assume 0-100 range unless specified
        
        last_passed_value = state.get("last_deadband_value")
        
        # If no previous value, let the first one through
        if last_passed_value is None:
            state["last_deadband_value"] = value
            return value

        # Calculate change
        try:
            val_float = float(value)
            last_val_float = float(last_passed_value)
            
            # Avoid division by zero if max_value is 0
            if max_value == 0:
                change_percent = 0 if val_float == last_val_float else 100
            else:
                change_percent = (abs(val_float - last_val_float) / max_value) * 100
            
            if change_percent < threshold_percent:
                return None # Drop
                
        except (ValueError, TypeError):
            # If values are not numbers, pass them through if they are different
            if value == last_passed_value:
                return None # Drop

        state["last_deadband_value"] = value
        return value
