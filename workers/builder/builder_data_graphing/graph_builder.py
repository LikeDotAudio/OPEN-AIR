# workers/builder/builder_data_graphing/graph_builder.py
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Dict, Any


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
