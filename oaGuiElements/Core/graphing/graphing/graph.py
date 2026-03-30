# graphing/graph.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module provides functions for creating the base Matplotlib plot within a Tkinter application.

import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Dict, Any

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

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
    if BUILDER_DEBUG:
        builder_logger.debug(f"🔬🏗️📊 [BUILDER] graph_builder: Creating base Matplotlib plot for '{config.get('path', 'Unknown')}'.")

    layout_config = config.get("layout", {})
    # ⚡ Enable transparency at the Figure level
    fig = Figure(
        figsize=(
            layout_config.get("width", 500) / 100,
            layout_config.get("height", 400) / 100,
        ),
        dpi=100,
        facecolor='none'
    )
    # ⚡ Enable transparency at the Axis level
    ax = fig.add_subplot(111, facecolor='none')

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()

    # ⚡ Ensure the Tkinter widget itself is configured for transparency
    # (Though it still needs the Industrial Transparency slice to look perfect)
    canvas_widget.configure(highlightthickness=0, bd=0)
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    return fig, ax, canvas
