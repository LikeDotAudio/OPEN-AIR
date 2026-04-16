# graphing/graph.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module provides functions for creating the base Matplotlib plot within a Tkinter application.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Dict, Any

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()


# Creates the base Matplotlib figure, axes, and canvas for embedding into a Tkinter frame.
# This function initializes a new Matplotlib figure and adds a subplot to it,
# then embeds this figure into a Tkinter canvas widget.
# Inputs:
#     parent_frame (tk.Frame): The Tkinter frame to embed the plot into.
#     config (Dict[str, Any]): A dictionary containing configuration settings for the plot,
#                              including layout dimensions.
# Outputs:
#     tuple: A tuple containing the Matplotlib figure, axes, and FigureCanvasTkAgg instance.
def create_base_plot(parent_frame: tk.Frame, config: Dict[str, Any]) -> tuple:
    """
    Creates the FigureCanvasTkAgg and basic Axis.
    Returns (figure, axis, canvas).
    """
    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] graph_builder: Creating base Matplotlib plot for '{config.get('path', 'Unknown')}'.", level="DEBUG")

    layout_config = config.get("layout", {})
    # ⚡ DIMENSION ENFORCEMENT: Use explicit geometry or layout, fallback to 500x400
    geom = config.get("geometry", {})
    width = config.get("width") or geom.get("width") or layout_config.get("width") or 500
    height = config.get("height") or geom.get("height") or layout_config.get("height") or 400
    
    # Ensure we don't start with 0 or 1 which triggers the "pixel wide" bug
    width = max(1, int(float(width)))
    height = max(1, int(float(height)))

    # ⚡ Enable transparency at the Figure level
    fig = Figure(
        figsize=(width / 100, height / 100),
        dpi=100,
        facecolor='none'
    )
    # ⚡ Enable transparency at the Axis level
    ax = fig.add_subplot(111, facecolor='none')

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()

    # ⚡ Ensure the Tkinter widget itself is configured for transparency
    # (Though it still needs the Industrial Transparency slice to look perfect)
    try:
        canvas_widget.configure(highlightthickness=0, bd=0)
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    except tk.TclError as e:
        matrix_log("UI", "GUI_ELEMENTS", "create_base_plot", f"⚠️ Canvas widget configuration skipped: {e}", "TRACE")

    return fig, ax, canvas
