# Core/value_processor.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

class ValueProcessor:
    """
    Standardizes value extraction and normalization for GUI/MQTT synchronization.
    Handles JSON key mapping and type-specific clamping.
    """

    @staticmethod
    def extract_value(data, config):
        """Extracts the raw value from a payload dictionary based on config keys."""
        data_key = config.get("key")
        if data_key and isinstance(data, dict):
            return data.get(data_key)
        return data.get("value", data.get("pos", None))

    @staticmethod
    def normalize(raw_value, tk_var, config):
        """Converts and clamps a raw value to the target variable's type and range."""
        if raw_value is None:
            return None

        widget_type = config.get("type", "")
        
        # 1. Boolean Normalization
        if (widget_type in ["_GuiButtonToggle", "_WinkButton", "_WinkButtonToggler"] or 
            isinstance(tk_var, tk.BooleanVar)):
            if isinstance(raw_value, bool):
                return raw_value
            val_str = str(raw_value).lower().strip()
            return val_str in ("true", "1", "on")

        # 2. Numeric Clamping
        if isinstance(tk_var, (tk.DoubleVar, tk.IntVar)):
            try:
                v_min = float(config.get("min", config.get("value_min", 0.0)))
                v_max = float(config.get("max", config.get("value_max", 100.0)))
                return max(v_min, min(v_max, float(raw_value)))
            except (ValueError, TypeError):
                return None

        # 3. Default Pass-through
        return raw_value
