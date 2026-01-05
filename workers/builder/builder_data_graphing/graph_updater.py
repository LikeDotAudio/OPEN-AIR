# workers/builder/builder_data_graphing/graph_updater.py
from collections import deque
from typing import List, Any, Dict

def update_graph_data(line: Any, x_data: deque, y_data: deque, new_x: float, new_y: float):
    """
    Efficiently updates the x and y data of a specific line.
    """
    x_data.append(new_x)
    y_data.append(new_y)
    line.set_data(list(x_data), list(y_data))

def load_initial_data(line: Any, x_data: deque, y_data: deque, x_values: List[float], y_values: List[float]):
    """Loads a complete set of initial data points for a specific dataset."""
    x_data.clear()
    y_data.clear()
    x_data.extend(x_values)
    y_data.extend(y_values)
    line.set_data(list(x_data), list(y_data))

def clear_plot_data(line: Any, x_data: deque, y_data: deque):
    """Clears data from a specific dataset."""
    x_data.clear()
    y_data.clear()
    line.set_data([], [])

def autoscale_and_redraw(ax: object, canvas: object):
    """Autoscales axes and redraws the canvas."""
    ax.relim()
    ax.autoscale_view()
    canvas.draw()