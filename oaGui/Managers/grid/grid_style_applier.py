# oaGui/Managers/grid/grid_style_applier.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Applies physical row and column configurations to a Tkinter frame.

def apply_grid_configurations(parent_frame, num_rows, num_cols, row_weights, column_sizing):
    """
    Physically configures grid weights and minimum sizes on the target frame.
    Adds a reactive spacer row if no other vertical weights are present.
    """
    # 1. Configure Rows
    for i in range(num_rows):
        weight = row_weights.get(i, 0)
        parent_frame.grid_rowconfigure(i, weight=weight, minsize=1)
        
    # ⚡ SPACER ROW: Only add if no other row requested expansion.
    if sum(row_weights.values()) == 0:
        parent_frame.grid_rowconfigure(num_rows, weight=1)

    # 2. Configure Columns
    for i in range(num_cols):
        sizing = column_sizing[i] if i < len(column_sizing) else {}
        weight = sizing.get("weight", 1)
        min_width = max(1, sizing.get("minwidth", 1))

        if sizing.get("maxwidth", 0) > 0:
            min_width = sizing["maxwidth"]
            weight = 0

        parent_frame.grid_columnconfigure(i, weight=weight, minsize=min_width)
