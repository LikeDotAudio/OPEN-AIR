# oaGui/Methods/grid_column_configurator.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Encapsulates Tkinter grid column management logic.

import tkinter as tk


class GridColumnConfigurator:
    """Encapsulates Tkinter grid column management logic."""
    @staticmethod
    def apply_sizing(container: tk.Widget, num_columns: int, sizing_info: list[dict]):
        """Configures grid weights and minimum sizes for the target container."""
        for col_idx in range(num_columns):
            info = sizing_info[col_idx] if col_idx < len(sizing_info) else {}
            weight = info.get("weight", 1)
            minwidth = info.get("minwidth", 0)
            maxwidth = info.get("maxwidth", 0)

            if maxwidth > 0:
                minwidth = maxwidth
                weight = 0

            container.grid_columnconfigure(col_idx, weight=weight, minsize=minwidth)
