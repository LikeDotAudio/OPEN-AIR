# Managers/engine_grid_layout_logic.py
# Author: Anthony Peter Kuzub
# Version: 1.0.2
#
# Description: Orchestrates the calculation and application of Tkinter grid configurations.

from oaLogging.Methods.matrix_gate import matrix_log
from .grid_dimension_calculator import calculate_grid_dimensions
from .grid_weight_analyzer import calculate_grid_row_weights
from .grid_style_applier import apply_grid_configurations

class GridTopologyConfigurator:
    """Orchestrates grid configuration via atomic services."""

    @staticmethod
    def configure(parent_frame, data, all_fields):
        """Standard pipeline for calculating and applying grid topology."""
        
        # 1. Initialization
        initial_cols = max(int(data.get("layout_columns", 0)), len(data.get("column_sizing", [])))
        if initial_cols <= 0: initial_cols = 1
        
        # 2. Dimensions
        num_rows, num_cols, _, _ = calculate_grid_dimensions(all_fields, initial_cols, 0, 0)
        
        # 3. Weights
        row_weights = calculate_grid_row_weights(all_fields, num_rows, 0, 0)
        
        matrix_log("gui", "gui_builder", "grid_config", 
                   f"🌐 Configuring Grid for {parent_frame}: {num_rows}x{num_cols}", "TRACE")

        # 4. Physical Application
        apply_grid_configurations(parent_frame, num_rows, num_cols, row_weights, data.get("column_sizing", []))

        return num_cols
