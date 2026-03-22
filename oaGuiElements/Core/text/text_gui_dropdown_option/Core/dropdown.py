# Core/dropdown.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class DropdownDataManager:
    """Manages parsing, sorting, and initial state selection for Dropdown options."""

    @staticmethod
    def get_display_label(opt_data, default_key):
        return opt_data.get("label_active") or opt_data.get("label") or default_key

    @classmethod
    def parse_options(cls, config):
        options_map = config.get("options", {})
        if isinstance(options_map, list): options_map = {}
        
        sorted_opts = sorted(options_map.items(), key=lambda item: str(item[1].get("value", item[0])))
        labels = [cls.get_display_label(opt, key) for key, opt in sorted_opts]
        values = [opt.get("value", key) for key, opt in sorted_opts]
        return options_map, labels, values

    @classmethod
    def determine_initial_state(cls, config, options_map, option_values):
        init_val = config.get("value_default")
        if init_val is None:
            sel_opt = next((opt for k, opt in options_map.items() if str(opt.get("selected", "no")).lower() in ["yes", "true"]), None)
            if sel_opt: init_val = sel_opt.get("value")
        
        if init_val is None and option_values: init_val = option_values[0]
        
        init_label = ""
        for k, opt in options_map.items():
            if str(opt.get("value", k)) == str(init_val):
                init_label = cls.get_display_label(opt, k); break
                
        return init_val, init_label
