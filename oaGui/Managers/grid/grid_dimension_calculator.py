# oaGui/Managers/grid/grid_dimension_calculator.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Calculates required grid rows and columns based on field layout data.

def calculate_grid_dimensions(all_fields, initial_cols, current_row, current_col):
    """
    Analyzes field metadata to determine the maximum required row and column indices.
    Supports auto-flow for fields without explicit layout coordinates.
    """
    max_r, max_c = 0, 0
    num_cols = initial_cols
    
    if not all_fields:
        return 1, 1, 0, 0

    for item in all_fields:
        value = item[1] if isinstance(item, tuple) and len(item) == 2 else item
        if isinstance(value, dict):
            layout = value.get("layout", {})
            field_row = layout.get("row", current_row)
            field_col = layout.get("column", current_col)
            col_span = int(layout.get("col_span", 1))
            row_span = int(layout.get("row_span", 1))

            max_r = max(max_r, field_row + row_span - 1)
            max_c = max(max_c, field_col + col_span - 1)

            # Auto-flow calculation for next field
            current_col = field_col + col_span
            if num_cols > 0 and current_col >= num_cols:
                current_col = 0
                current_row = field_row + row_span

    # Final dimension count (1-based)
    final_cols = max(num_cols, max_c + 1)
    final_rows = max_r + 1
    
    return max(1, final_rows), max(1, final_cols), max_r, max_c
