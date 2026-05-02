# oaGui/Managers/grid/grid_weight_analyzer.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Analyzes widget types and layout metadata to determine optimal row weights.

def calculate_grid_row_weights(all_fields, num_rows, initial_row, initial_col):
    """
    Scans fields to determine which rows should expand vertically (weight=1).
    Heuristically assigns weights to structural and expanding widget types.
    """
    row_weights = {i: 0 for i in range(num_rows)}
    
    if not all_fields:
        return row_weights

    current_row, current_col = initial_row, initial_col
    
    # Standard expanding widget types
    expanding_types = {
        "OcaBin", "Bin", "OcaBlock", "Block", "OcaArray", "Array",
        "OcaCollapsibleBlock", "plot_widget", 
        "_Horizontal_with_dial_Value", "_CustomLTP", "_Fader", 
        "_SmartFader", "_CustomFader", "_CustomDualVerticalFader", 
        "_CompositeFader", "_FaderWithBarGraph", "_BarGraph", 
        "_SmartMeter", "MeterBar", "_MeterBar", "_VUMeterKnob", 
        "_NeedleVUMeter", "_MDP", "_CMDP", "SelectorSwitch", 
        "_SelectorSwitch"
    }

    for item in all_fields:
        value = item[1] if isinstance(item, tuple) and len(item) == 2 else item
        if not isinstance(value, dict): continue
        
        layout = value.get("layout", {})
        field_row = layout.get("row", current_row)
        row_span = int(layout.get("row_span", 1))
        widget_type = value.get("type", "")
        
        # Determine weight
        default_weight = 1 if widget_type in expanding_types else 0
        weight_y = int(layout.get("weight_y", default_weight))
        
        # Forced zero for separators
        if "Fold" in widget_type or "Break" in widget_type:
            weight_y = 0

        # Apply to target row (usually the last row of a span)
        target_idx = field_row + row_span - 1
        if target_idx in row_weights:
            row_weights[target_idx] = max(row_weights[target_idx], weight_y)

        # Update auto-flow tracker for weight discovery consistency
        field_col = layout.get("column", current_col)
        col_span = int(layout.get("col_span", 1))
        # Note: num_cols is not used here but could be passed if needed for wrap logic
        # For simplicity, we just track current_row
        current_col = field_col + col_span
        # We don't have num_cols here, but auto-flow logic should match calculator
        
    return row_weights
