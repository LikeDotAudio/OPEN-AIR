# Core/grid_topology_configurator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Handles the calculation and application of Tkinter grid configurations.

class GridTopologyConfigurator:
    """Handles the calculation and application of Tkinter grid configurations."""

    @staticmethod
    def configure(parent_frame, data, all_fields):
        """Calculates grid dimensions and configures row/column weights."""
        max_r, max_c = 0, 0

        # 1. Determine base column count from explicit settings
        explicit_cols = int(data.get("layout_columns", 0))
        col_sizing = data.get("column_sizing", [])

        # ⚡ VERTICAL DEFAULT: If no columns specified, default to 1 for vertical stacking.
        # This prevents infinite horizontal flow when layout_columns is missing.
        num_cols = max(explicit_cols, len(col_sizing))
        is_auto_flow = (num_cols <= 0)
        if is_auto_flow:
            num_cols = 1

        # 2. Calculate required columns/rows based on fields
        if all_fields:
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
                    max_c = max(max_c, cc + cs - 1)

                    # Auto-flow calculation
                    c = cc + cs
                    if num_cols > 0 and c >= num_cols:
                        c = 0; r = cr + rs

        # Final column count: prioritized explicit > discovered
        if num_cols <= 0:
            num_cols = max_c + 1

        # ⚡ MINIMUM SAFETY: Ensure at least one cell exists
        num_rows = max_r + 1
        if num_rows <= 0: num_rows = 1
        if num_cols <= 0: num_cols = 1

        # 🎯 ROW WEIGHTS: Calculate weights to avoid vertical 'bloat'
        row_weights = {i: 0 for i in range(num_rows)}
        if all_fields:
            r, c = 0, 0
            for item in all_fields:
                value = item[1] if isinstance(item, tuple) and len(item) == 2 else item
                if isinstance(value, dict):
                    lay = value.get("layout", {})
                    cr = lay.get("row", r)
                    rs = int(lay.get("row_span", 1))
                    
                    w_type = value.get("type", "")
                    
                    # ⚡ SMART DEFAULTS: Certain structural/expanding widgets default to weight_y=1.
                    # Other widgets (sliders, text) default to 0 to remain tight.
                    default_wy = 0
                    if w_type in ["OcaBin", "Bin", "OcaBlock", "Block", "plot_widget", "_Horizontal_with_dial_Value"]:
                        default_wy = 1
                        
                    wy = int(lay.get("weight_y", default_wy))
                    
                    if "Fold" in w_type or "Break" in w_type:
                        wy = 0 # Force 0 for separators

                    row_weights[cr + rs - 1] = max(row_weights[cr + rs - 1], wy)

                    # Auto-flow calculation
                    cc = lay.get("column", c)
                    cs = int(lay.get("col_span", 1))
                    c = cc + cs
                    if num_cols > 0 and c >= num_cols:
                        c = 0; r = cr + rs

        from oaLogging.Methods.matrix_gate import matrix_log
        matrix_log("gui", "gui_builder", "grid_config", f"🌐 Configuring Grid for {parent_frame}: {num_rows}x{num_cols}", "TRACE")

        # 1. Configure Rows
        for i in range(num_rows):
            weight = row_weights.get(i, 0)
            parent_frame.grid_rowconfigure(i, weight=weight, minsize=1)
            
        # ⚡ SPACER ROW: Only add if no other row requested expansion.
        # This pushes non-expanding content to the top without squishing expanding content.
        if sum(row_weights.values()) == 0:
            parent_frame.grid_rowconfigure(num_rows, weight=1)

        # 2. Configure Columns
        for i in range(num_cols):
            sz = col_sizing[i] if i < len(col_sizing) else {}
            weight = sz.get("weight", 1)
            minw = sz.get("minwidth", 1)
            if minw <= 0: minw = 1

            if sz.get("maxwidth", 0) > 0:
                minw = sz["maxwidth"]
                weight = 0

            parent_frame.grid_columnconfigure(i, weight=weight, minsize=minw)

        return num_cols
