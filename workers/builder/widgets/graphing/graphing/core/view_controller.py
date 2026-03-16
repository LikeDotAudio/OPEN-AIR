from matplotlib.patches import Rectangle
from tkinter import simpledialog

class ViewController:
    """Manages Zoom and Pan logic for Matplotlib axes."""

    def __init__(self, ax, callbacks=None, on_context_menu=None):
        self.ax, self.callbacks, self.on_context_menu_callback = ax, callbacks, on_context_menu
        self.press = self.rect = self.rect_start = self.cur_xlim = self.cur_ylim = self.axis_mode = self.pan_axis_mode = None
        self.initial_xlim, self.initial_ylim = ax.get_xlim(), ax.get_ylim()

    def on_press(self, event):
        if event.inaxes != self.ax:
            bbox, x, y = self.ax.bbox, event.x, event.y
            if event.dblclick:
                if event.button == 1: self._handle_axis_dblclick(x, y, bbox)
                else: self.reset_view()
                return
            if event.button in [1, 2]: self._set_axis_mode(x, y, bbox, event.button)
            return 
        
        if event.button == 2: self.cur_xlim, self.cur_ylim, self.press = self.ax.get_xlim(), self.ax.get_ylim(), (event.x, event.y)
        elif event.button == 3:
            self.rect_start = (event.xdata, event.ydata)
            self.rect = Rectangle((event.xdata, event.ydata), 0, 0, linewidth=1, edgecolor='white', facecolor=(1, 1, 1, 0.2))
            self.ax.add_patch(self.rect); self.ax.figure.canvas.draw_idle()

    def on_release(self, event):
        if self.axis_mode or self.pan_axis_mode: self.axis_mode = self.pan_axis_mode = self.press = None; self._trigger(); return
        if self.press and event.button == 2: self.press = None; self.ax.figure.canvas.draw(); self._trigger()
        if self.rect and event.button == 3:
            x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata
            self.rect.remove(); self.rect = self.rect_start = None
            if x0 is not None and x1 is not None and x0 != x1 and y0 != y1:
                 self.ax.set_xlim(min(x0, x1), max(x0, x1)); self.ax.set_ylim(min(y0, y1), max(y0, y1))
                 self.ax.figure.canvas.draw_idle(); self._trigger()
            elif self.on_context_menu_callback: self.on_context_menu_callback(event)

    def on_motion(self, event):
        if (self.axis_mode or self.pan_axis_mode) and self.press:
            x_start, y_start = self.press; w, h = self.ax.bbox.width, self.ax.bbox.height
            if self.axis_mode:
                if self.axis_mode == 'x': s = max(0.1, 1.0 - ((event.x - x_start)/500.0)); vmin, vmax = self.cur_xlim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_xlim(c-sp, c+sp)
                else: s = max(0.1, 1.0 - ((event.y - y_start)/500.0)); vmin, vmax = self.cur_ylim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_ylim(c-sp, c+sp)
            else:
                if self.pan_axis_mode == 'x' and w > 0: dx = ((self.cur_xlim[1]-self.cur_xlim[0])/w)*(event.x-x_start); self.ax.set_xlim(self.cur_xlim[0]-dx, self.cur_xlim[1]-dx)
                elif h > 0: dy = ((self.cur_ylim[1]-self.cur_ylim[0])/h)*(event.y-y_start); self.ax.set_ylim(self.cur_ylim[0]-dy, self.cur_ylim[1]-dy)
            self.ax.figure.canvas.draw_idle(); return

        if event.inaxes == self.ax:
            if self.press and event.button == 2:
                dx = ((self.cur_xlim[1]-self.cur_xlim[0])/self.ax.bbox.width)*(event.x-self.press[0])
                dy = ((self.cur_ylim[1]-self.cur_ylim[0])/self.ax.bbox.height)*(event.y-self.press[1])
                self.ax.set_xlim(self.cur_xlim[0]-dx, self.cur_xlim[1]-dx); self.ax.set_ylim(self.cur_ylim[0]-dy, self.cur_ylim[1]-dy)
                self.ax.figure.canvas.draw_idle()
            elif self.rect:
                x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata
                self.rect.set_width(abs(x1-x0)); self.rect.set_height(abs(y1-y0)); self.rect.set_xy((min(x0,x1), min(y0,y1))); self.ax.figure.canvas.draw_idle()

    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        f = 1/1.1 if event.button == "up" else 1.1; cur_x, cur_y = self.ax.get_xlim(), self.ax.get_ylim(); xd, yd = event.xdata, event.ydata
        self.ax.set_xlim(xd*(cur_x[0]/xd)**f, xd*(cur_x[1]/xd)**f) if self.ax.get_xscale()=='log' else self.ax.set_xlim((cur_x[0]-xd)*f+xd, (cur_x[1]-xd)*f+xd)
        self.ax.set_ylim(yd*(cur_y[0]/yd)**f, yd*(cur_y[1]/yd)**f) if self.ax.get_yscale()=='log' else self.ax.set_ylim((cur_y[0]-yd)*f+yd, (cur_y[1]-yd)*f+yd)
        self.ax.figure.canvas.draw(); self._trigger()

    def reset_view(self):
        self.ax.set_xlim(self.initial_xlim); self.ax.set_ylim(self.initial_ylim)
        self.ax.figure.canvas.draw(); self._trigger()

    def _trigger(self):
        if self.callbacks and "on_view_change" in self.callbacks: self.callbacks["on_view_change"](self.ax.get_xlim(), self.ax.get_ylim())

    def _handle_axis_dblclick(self, x, y, bbox):
        if bbox.x0 <= x <= bbox.x1:
            if bbox.y0-80 < y < bbox.y0: self._ask_lim('x', 'min')
            elif y > bbox.y1: self._ask_lim('y', 'max')
        elif bbox.y0 <= y <= bbox.y1:
            if bbox.x0-80 < x < bbox.x0: self._ask_lim('y', 'min')
            elif x > bbox.x1: self._ask_lim('x', 'max')

    def _ask_lim(self, a, s):
        curr = self.ax.get_xlim() if a == 'x' else self.ax.get_ylim(); idx = 0 if s == 'min' else 1
        v = simpledialog.askfloat("Limit", f"{a.upper()} {s}:", initialvalue=curr[idx])
        if v is not None:
            if a == 'x': self.ax.set_xlim(left=v) if s == 'min' else self.ax.set_xlim(right=v)
            else: self.ax.set_ylim(bottom=v) if s == 'min' else self.ax.set_ylim(top=v)
            self.ax.figure.canvas.draw_idle(); self._trigger()

    def _set_axis_mode(self, x, y, bbox, btn):
        mode = 'axis_mode' if btn == 1 else 'pan_axis_mode'
        if (bbox.x0 <= x <= bbox.x1) and (bbox.y0-80 < y < bbox.y0 or y > bbox.y1): setattr(self, mode, 'x'); self.press, self.cur_xlim = (x,y), self.ax.get_xlim()
        elif (bbox.y0 <= y <= bbox.y1) and (bbox.x0-80 < x < bbox.x0 or x > bbox.x1): setattr(self, mode, 'y'); self.press, self.cur_ylim = (x,y), self.ax.get_ylim()
