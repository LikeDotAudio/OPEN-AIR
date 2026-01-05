# workers/builder/builder_data_graphing/graph_interactor.py
from matplotlib.backend_bases import NavigationToolbar2
from typing import Dict, Any

class ZoomPan:
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

        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)

    def on_press(self, event):
        if event.inaxes != self.ax: return
        self.cur_xlim = self.ax.get_xlim()
        self.cur_ylim = self.ax.get_ylim()
        self.press = self.x0, self.y0, event.xdata, event.ydata
        self.x0, self.y0, self.xpress, self.ypress = self.press

    def on_release(self, event):
        self.press = None
        self.ax.figure.canvas.draw()

    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax: return
        dx = event.xdata - self.xpress
        dy = event.ydata - self.ypress
        self.cur_xlim -= dx
        self.cur_ylim -= dy
        self.ax.set_xlim(self.cur_xlim)
        self.ax.set_ylim(self.cur_ylim)
        self.ax.figure.canvas.draw()

    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        scale_factor = 1.1 if event.button == 'up' else 1 / 1.1
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        new_xlim = (
            (cur_xlim[0] - event.xdata) * scale_factor + event.xdata,
            (cur_xlim[1] - event.xdata) * scale_factor + event.xdata
        )
        new_ylim = (
            (cur_ylim[0] - event.ydata) * scale_factor + event.ydata,
            (cur_ylim[1] - event.ydata) * scale_factor + event.ydata
        )

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.ax.figure.canvas.draw()

def setup_interaction(fig: object, ax: object, interaction_config: Dict[str, Any]):
    """
    Binds events for mouse movement and scrolling.
    """
    if interaction_config.get("enable_zoom") or interaction_config.get("enable_pan"):
        ZoomPan(ax)

    if interaction_config.get("show_hover_value"):
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def on_mouse_hover(event):
            update_annotation(event, ax, annot)

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_hover)

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