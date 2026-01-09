# builder_data_graphing/graph_updater.py
#
# This module provides utility functions for efficiently updating and redrawing Matplotlib graphs.
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
from collections import deque
from typing import List, Any, Dict


# Efficiently updates the x and y data of a specific plot line.
# This function appends new data points to the data deques and updates the Matplotlib line object,
# making it suitable for real-time plotting.
# Inputs:
#     line (Any): The Matplotlib line object to update.
#     x_data (deque): A deque containing x-axis data points.
#     y_data (deque): A deque containing y-axis data points.
#     new_x (float): The new x-axis data point.
#     new_y (float): The new y-axis data point.
# Outputs:
#     None.
def update_graph_data(
    line: Any, x_data: deque, y_data: deque, new_x: float, new_y: float
):
    """
    Efficiently updates the x and y data of a specific line.
    """
    x_data.append(new_x)
    y_data.append(new_y)
    line.set_data(list(x_data), list(y_data))


# Loads a complete set of initial data points for a specific dataset.
# This function clears any existing data in the deques and extends them with the provided
# lists of x and y values, then updates the Matplotlib line object.
# Inputs:
#     line (Any): The Matplotlib line object to update.
#     x_data (deque): A deque containing x-axis data points.
#     y_data (deque): A deque containing y-axis data points.
#     x_values (List[float]): A list of initial x-axis values.
#     y_values (List[float]): A list of initial y-axis values.
# Outputs:
#     None.
def load_initial_data(
    line: Any,
    x_data: deque,
    y_data: deque,
    x_values: List[float],
    y_values: List[float],
):
    """Loads a complete set of initial data points for a specific dataset."""
    x_data.clear()
    y_data.clear()
    x_data.extend(x_values)
    y_data.extend(y_values)
    line.set_data(list(x_data), list(y_data))


# Clears all data from a specific plot line.
# This function empties the data deques and resets the Matplotlib line object to display no data.
# Inputs:
#     line (Any): The Matplotlib line object to clear.
#     x_data (deque): A deque containing x-axis data points.
#     y_data (deque): A deque containing y-axis data points.
# Outputs:
#     None.
def clear_plot_data(line: Any, x_data: deque, y_data: deque):
    """Clears data from a specific dataset."""
    x_data.clear()
    y_data.clear()
    line.set_data([], [])


# Autoscales the axes and redraws the canvas.
# This function adjusts the axis limits to fit the current data and refreshes the
# Matplotlib canvas to display the updated plot.
# Inputs:
#     ax (object): The Matplotlib axes object.
#     canvas (object): The Matplotlib FigureCanvasTkAgg object.
# Outputs:
#     None.
def autoscale_and_redraw(ax: object, canvas: object):
    """Autoscales axes and redraws the canvas."""
    ax.relim()
    ax.autoscale_view()
    canvas.draw()