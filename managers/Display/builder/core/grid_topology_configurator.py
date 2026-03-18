class GridTopologyConfigurator:
    """Handles the calculation and application of Tkinter grid configurations."""

    @staticmethod
    def configure(parent_frame, data, all_fields):
        """Calculates grid dimensions and configures row/column weights."""
        max_r, max_c = 0, 0
        if all_fields:
            for item in all_fields:
                # Handle both (key, val) pairs and raw values (if list was processed)
                val = item[1] if isinstance(item, tuple) and len(item) == 2 else item
                
                if isinstance(val, dict):
                    lay = val.get("layout", {})
                    max_r = max(max_r, lay.get("row", 0) + lay.get("row_span", 1) - 1)
                    max_c = max(max_c, lay.get("column", 0) + lay.get("col_span", 1) - 1)
        
        num_cols = int(data.get("layout_columns", max_c + 1))
        num_rows = max_r + 1

        # 1. Configure Rows
        for i in range(num_rows): parent_frame.grid_rowconfigure(i, weight=1)

        # 2. Configure Columns
        col_sizing = data.get("column_sizing", [])
        for i in range(num_cols):
            sz = col_sizing[i] if i < len(col_sizing) else {}
            weight, minw = sz.get("weight", 1), sz.get("minwidth", 0)
            if sz.get("maxwidth", 0) > 0: minw, weight = sz["maxwidth"], 0
            parent_frame.grid_columnconfigure(i, weight=weight, minsize=minw)
            
        return num_cols
