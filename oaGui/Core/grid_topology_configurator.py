# Core/grid_topology_configurator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class GridTopologyConfigurator:
    """Handles the calculation and application of Tkinter grid configurations."""

    @staticmethod
    def configure(parent_frame, data, all_fields):
        """Calculates grid dimensions and configures row/column weights."""
        max_r, max_c = 0, 0
        num_cols = int(data.get("layout_columns", 0))

        if all_fields:
            if num_cols <= 0:
                for item in all_fields:
                    value = item[1] if isinstance(item, tuple) and len(item) == 2 else item
                    if isinstance(value, dict):
                        lay = value.get("layout", {})
                        max_c = max(max_c, lay.get("column", 0) + lay.get("col_span", 1) - 1)
                num_cols = max_c + 1

            r, c = 0, 0
            for item in all_fields:
                value = item[1] if isinstance(item, tuple) and len(item) == 2 else item
                if isinstance(value, dict):
                    lay = value.get("layout", {})
                    cr = lay.get("row", r)
                    cc = lay.get("column", c)
                    cs = int(lay.get("col_span", 1))
                    rs = int(lay.get("row_span", 1))
                    
                    max_r = max(max_r, cr + rs - 1)
                    
                    c = cc + cs
                    if c >= num_cols:
                        c = 0
                        r = cr + rs

        num_cols = max_c + 1

        from oaLogging.Methods.matrix_gate import matrix_log
        matrix_log("gui", "gui_builder", "grid_config", f"🌐 Configuring Grid for {parent_frame}: {max_r+1}x{num_cols}", "TRACE")

        num_rows = max_r + 1

        # ⚡ EXPANSION FIX: Ensure at least one row/column has weight if the list is empty (for structural bins)
        if num_rows == 0: num_rows = 1
        if num_cols == 0: num_cols = 1

        # 1. Configure Rows
        for i in range(num_rows): parent_frame.grid_rowconfigure(i, weight=1, minsize=1)

        # 2. Configure Columns
        from oaLogging.Methods.matrix_gate import matrix_log
        col_sizing = data.get("column_sizing", [])
        for i in range(num_cols):
            sz = col_sizing[i] if i < len(col_sizing) else {}
            weight, minw = sz.get("weight", 1), sz.get("minwidth", 1)
            if minw <= 0: minw = 1
            if sz.get("maxwidth", 0) > 0: minw, weight = sz["maxwidth"], 0
            parent_frame.grid_columnconfigure(i, weight=weight, minsize=minw)
            matrix_log("gui", "gui_builder", "grid_config", f"  ├─ Col {i}: weight={weight}, min={minw}", "TRACE")
            
        return num_cols
