# builder_data_graphing/graph_builder.py
#
# This module provides functions for creating the base Matplotlib plot within a Tkinter application.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Dict, Any


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
    layout_config = config.get("layout", {})
    fig = Figure(
        figsize=(
            layout_config.get("width", 5) / 100,
            layout_config.get("height", 4) / 100,
        ),
        dpi=100,
    )
    ax = fig.add_subplot(111)

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    return fig, ax, canvas