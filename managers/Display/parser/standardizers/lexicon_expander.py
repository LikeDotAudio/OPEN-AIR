class LexiconExpander:
    """
    Maps Lexicon Abbreviations to engine-expected keys.
    """
    MAPPING = {
        "lbl": "label",
        "w": "width",
        "h": "height",
        "W": "width",
        "H": "height",
        "columns": "layout_columns",
        "colspan": "col_span",
        "rowspan": "row_span",
        "pad": "padding",
        "val": "value_default",
        "min": "min",
        "max": "max",
        "unit": "units",
        "sub": "path",
        "pub": "publish_path",
        "poll": "poll",
        "bg": "bg_color",
        "fg": "text_color"
    }

    @classmethod
    def expand(cls, data):
        """
        Recursively expands abbreviations in a dictionary.
        """
        if not isinstance(data, dict):
            return data
        
        new_data = {}
        for k, v in data.items():
            if isinstance(v, dict):
                v = cls.expand(v)
            
            target_key = cls.MAPPING.get(k, k)
            
            # ⚡ SPECIAL HANDLING: x/y should ONLY be row/column in a layout context
            if k == "x":
                if any(key in data for key in ["sticky", "weight", "col_span"]):
                    target_key = "row"
                else:
                    target_key = "width" # Fallback for cap.x etc.
            elif k == "y":
                if any(key in data for key in ["sticky", "weight", "row_span"]):
                    target_key = "column"
                else:
                    target_key = "height" # Fallback for cap.y etc.

            if target_key not in new_data or target_key == k:
                new_data[target_key] = v
        
        return new_data
