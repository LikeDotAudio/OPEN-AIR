# Core/grid.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaGuiElements.Constants.gui_constants import (
    DEFAULT_COLUMN_SPACING, 
    GRID_ROW_WEIGHT_TOP, 
    GRID_ROW_WEIGHT_BOTTOM, 
    GRID_ROW_MINSIZE_TOP, 
    GRID_ROW_MINSIZE_BOTTOM,
    KNOB_SAFE_DIM_MIN,
    KNOB_SAFE_DIM_MAX,
    KNOB_SAFE_DIM_DEFAULT,
    V_WIDTH_LIMIT_RATIO
)

class GridManager:
    """Calculates and configures column and row weights for the composite widget."""

    @staticmethod
    def configure(container, config_data, w_req):
        """Sets up the 3-column, 2-row grid structure and calculates safe pixel limits."""
        spacing = config_data.get("column_spacing", DEFAULT_COLUMN_SPACING)
        if not isinstance(spacing, list) or len(spacing) < 3:
            spacing = DEFAULT_COLUMN_SPACING

        container.grid_columnconfigure(0, weight=int(spacing[0]), uniform="col")
        container.grid_columnconfigure(1, weight=int(spacing[1]), uniform="col")
        container.grid_columnconfigure(2, weight=int(spacing[2]), uniform="col")

        container.grid_rowconfigure(0, weight=GRID_ROW_WEIGHT_TOP, minsize=GRID_ROW_MINSIZE_TOP)
        container.grid_rowconfigure(1, weight=GRID_ROW_WEIGHT_BOTTOM, minsize=GRID_ROW_MINSIZE_BOTTOM)

        col_1_w = (w_req * spacing[1]) / sum(spacing)
        col_2_w = (w_req * spacing[2]) / sum(spacing)

        safe_knob_dim = int(col_1_w * 0.9) if col_1_w > 0 else KNOB_SAFE_DIM_DEFAULT
        safe_knob_dim = max(KNOB_SAFE_DIM_MIN, min(KNOB_SAFE_DIM_MAX, safe_knob_dim))

        v_width_limit = int(col_2_w / V_WIDTH_LIMIT_RATIO) - 1 if col_2_w > 0 else V_WIDTH_LIMIT_RATIO

        return safe_knob_dim, v_width_limit
