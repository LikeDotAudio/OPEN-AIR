# builder_data_graphing/graph_interactor.py
#
# This module provides functions for setting up interactive features on Matplotlib graphs, including zoom, pan, and hover annotations.
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
from matplotlib.backend_bases import NavigationToolbar2
from typing import Dict, Any


class ZoomPan:
    # Initializes the ZoomPan functionality for a Matplotlib axis.
    # This sets up event listeners for mouse presses, releases, motion, and scrolling
    # to enable interactive zooming and panning on the graph.
    # Inputs:
    #     ax: The Matplotlib axes object to apply interaction to.
    # Outputs:
    #     None.
    def __init__(self, ax):
        self.ax = ax
        self.fig = ax.get_figure()
        self.press = None
        self.cur_xlim = None
        self.cur_ylim = None
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.xpress = None
        self.ypress = None

        self.fig.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)

    # Handles the mouse button press event for panning.
    # This method records the initial cursor position and the current axis limits
    # to be used as a reference for dragging.
    # Inputs:
    #     event: The Matplotlib mouse event object.
    # Outputs:
    #     None.
    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        self.cur_xlim = self.ax.get_xlim()
        self.cur_ylim = self.ax.get_ylim()
        self.press = self.x0, self.y0, event.xdata, event.ydata
        self.x0, self.y0, self.xpress, self.ypress = self.press

    # Handles the mouse button release event.
    # This method clears the press state, indicating the end of a pan or zoom operation,
    # and redraws the canvas.
    # Inputs:
    #     event: The Matplotlib mouse event object.
    # Outputs:
    #     None.
    def on_release(self, event):
        self.press = None
        self.ax.figure.canvas.draw()

    # Handles the mouse motion event for panning.
    # If a mouse button is pressed, this method calculates the displacement
    # and updates the axis limits to pan the view accordingly.
    # Inputs:
    #     event: The Matplotlib mouse event object.
    # Outputs:
    #     None.
    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax:
            return
        dx = event.xdata - self.xpress
        dy = event.ydata - self.ypress
        self.cur_xlim -= dx
        self.cur_ylim -= dy
        self.ax.set_xlim(self.cur_xlim)
        self.ax.set_ylim(self.cur_ylim)
        self.ax.figure.canvas.draw()

    # Handles the mouse scroll event for zooming.
    # This method adjusts the axis limits based on the scroll direction and a scale factor,
    # effectively zooming in or out around the cursor's position.
    # Inputs:
    #     event: The Matplotlib scroll event object.
    # Outputs:
    #     None.
    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        scale_factor = 1.1 if event.button == "up" else 1 / 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        new_xlim = (
            (cur_xlim[0] - event.xdata) * scale_factor + event.xdata,
            (cur_xlim[1] - event.xdata) * scale_factor + event.xdata,
        )
        new_ylim = (
            (cur_ylim[0] - event.ydata) * scale_factor + event.ydata,
            (cur_ylim[1] - event.ydata) * scale_factor + event.ydata,
        )

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.ax.figure.canvas.draw()


# Sets up interactive features for a Matplotlib graph.
# This function enables zoom and pan functionality using the ZoomPan class,
# and can optionally display hover annotations to show data values when the mouse
# hovers over the plot area.
# Inputs:
#     fig (object): The Matplotlib figure object.
#     ax (object): The Matplotlib axes object.
#     interaction_config (Dict[str, Any]): A dictionary specifying which interactions to enable.
# Outputs:
#     None.
def setup_interaction(fig: object, ax: object, interaction_config: Dict[str, Any]):
    """
    Binds events for mouse movement and scrolling.
    """
    if interaction_config.get("enable_zoom") or interaction_config.get("enable_pan"):
        ZoomPan(ax)

    if interaction_config.get("show_hover_value"):
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(20, 20),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"),
            arrowprops=dict(arrowstyle="->"),
        )
        annot.set_visible(False)

        def on_mouse_hover(event):
            update_annotation(event, ax, annot)

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_hover)


# Updates the annotation box when the mouse hovers over a data point.
# This function sets the position and text of a Matplotlib annotation box to display
# the x and y coordinates of the mouse cursor when it is within the plot area.
# Inputs:
#     event: The Matplotlib mouse event object.
#     ax: The Matplotlib axes object.
#     annot: The Matplotlib annotation object.
# Outputs:
#     None.
def update_annotation(event, ax, annot):
    """Updates the annotation box when mouse hovers over a point."""
    if event.inaxes == ax:
        # For simplicity, we are not snapping to the line.
        # A more advanced implementation would find the nearest point on the line.
        annot.xy = (event.xdata, event.ydata)
        annot.set_text(f"x={event.xdata:.2f}, y={event.ydata:.2f}")
        annot.set_visible(True)
        ax.figure.canvas.draw_idle()
    else:
        if annot.get_visible():
            annot.set_visible(False)
            ax.figure.canvas.draw_idle()