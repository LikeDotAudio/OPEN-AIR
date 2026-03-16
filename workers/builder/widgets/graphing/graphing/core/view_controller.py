from matplotlib.patches import Rectangle
from tkinter import simpledialog

# Mouse Button Constants
LEFT_CLICK = 1
MIDDLE_CLICK = 2
RIGHT_CLICK = 3

# Zoom and Pan Constants
DEFAULT_ZOOM_FACTOR = 1.1
MINIMUM_ZOOM_SCALE = 0.1
NORMAL_ZOOM_SCALE = 1.0
ZOOM_SENSITIVITY_DIVISOR = 500.0
RECTANGLE_FACE_ALPHA = 0.2
AXIS_CLICK_THRESHOLD_PIXELS = 80

class ViewController:
    """Manages Zoom and Pan logic for Matplotlib axes."""

    def __init__(self, axes, event_callbacks=None, on_context_menu=None):
        self.axes = axes
        self.event_callbacks = event_callbacks
        self.on_context_menu_callback = on_context_menu
        
        self.mouse_press_position = None
        self.selection_rectangle = None
        self.selection_rectangle_start = None
        self.current_xlim = None
        self.current_ylim = None
        self.active_axis_zoom_mode = None
        self.active_axis_pan_mode = None
        
        self.initial_xlim = axes.get_xlim()
        self.initial_ylim = axes.get_ylim()

    def handle_mouse_press(self, event):
        """Handles mouse button press events for zooming and panning."""
        if event.inaxes != self.axes:
            axes_bbox = self.axes.bbox
            mouse_x, mouse_y = event.x, event.y
            
            if event.dblclick:
                if event.button == LEFT_CLICK:
                    self._handle_axis_double_click(mouse_x, mouse_y, axes_bbox)
                else:
                    self.reset_view()
                return
            
            if event.button in [LEFT_CLICK, MIDDLE_CLICK]:
                self._initialize_axis_mode(mouse_x, mouse_y, axes_bbox, event.button)
            return 
        
        if event.button == MIDDLE_CLICK:
            self.current_xlim = self.axes.get_xlim()
            self.current_ylim = self.axes.get_ylim()
            self.mouse_press_position = (event.x, event.y)
        elif event.button == RIGHT_CLICK:
            self.selection_rectangle_start = (event.xdata, event.ydata)
            self.selection_rectangle = Rectangle(
                (event.xdata, event.ydata), 0, 0, 
                linewidth=1, edgecolor='white', facecolor=(1, 1, 1, RECTANGLE_FACE_ALPHA)
            )
            self.axes.add_patch(self.selection_rectangle)
            self.axes.figure.canvas.draw_idle()

    def handle_mouse_release(self, event):
        """Handles mouse button release events to finalize zooming and panning."""
        if self.active_axis_zoom_mode or self.active_axis_pan_mode:
            self.active_axis_zoom_mode = self.active_axis_pan_mode = self.mouse_press_position = None
            self._notify_view_change()
            return
            
        if self.mouse_press_position and event.button == MIDDLE_CLICK:
            self.mouse_press_position = None
            self.axes.figure.canvas.draw()
            self._notify_view_change()
            
        if self.selection_rectangle and event.button == RIGHT_CLICK:
            start_x, start_y = self.selection_rectangle_start
            end_x, end_y = event.xdata, event.ydata
            
            self.selection_rectangle.remove()
            self.selection_rectangle = self.selection_rectangle_start = None
            
            if start_x is not None and end_x is not None and start_x != end_x and start_y != end_y:
                 self.axes.set_xlim(min(start_x, end_x), max(start_x, end_x))
                 self.axes.set_ylim(min(start_y, end_y), max(start_y, end_y))
                 self.axes.figure.canvas.draw_idle()
                 self._notify_view_change()
            elif self.on_context_menu_callback:
                self.on_context_menu_callback(event)

    def handle_mouse_motion(self, event):
        """Handles mouse motion events for real-time zooming and panning."""
        if (self.active_axis_zoom_mode or self.active_axis_pan_mode) and self.mouse_press_position:
            press_x, press_y = self.mouse_press_position
            axes_width = self.axes.bbox.width
            axes_height = self.axes.bbox.height
            
            if self.active_axis_zoom_mode:
                if self.active_axis_zoom_mode == 'x':
                    zoom_scale = max(MINIMUM_ZOOM_SCALE, NORMAL_ZOOM_SCALE - ((event.x - press_x) / ZOOM_SENSITIVITY_DIVISOR))
                    min_val, max_val = self.current_xlim
                    center = (min_val + max_val) / 2
                    span = ((max_val - min_val) / 2) * zoom_scale
                    self.axes.set_xlim(center - span, center + span)
                else:
                    zoom_scale = max(MINIMUM_ZOOM_SCALE, NORMAL_ZOOM_SCALE - ((event.y - press_y) / ZOOM_SENSITIVITY_DIVISOR))
                    min_val, max_val = self.current_ylim
                    center = (min_val + max_val) / 2
                    span = ((max_val - min_val) / 2) * zoom_scale
                    self.axes.set_ylim(center - span, center + span)
            else:
                if self.active_axis_pan_mode == 'x' and axes_width > 0:
                    delta_x = ((self.current_xlim[1] - self.current_xlim[0]) / axes_width) * (event.x - press_x)
                    self.axes.set_xlim(self.current_xlim[0] - delta_x, self.current_xlim[1] - delta_x)
                elif axes_height > 0:
                    delta_y = ((self.current_ylim[1] - self.current_ylim[0]) / axes_height) * (event.y - press_y)
                    self.axes.set_ylim(self.current_ylim[0] - delta_y, self.current_ylim[1] - delta_y)
            
            self.axes.figure.canvas.draw_idle()
            return

        if event.inaxes == self.axes:
            if self.mouse_press_position and event.button == MIDDLE_CLICK:
                delta_x = ((self.current_xlim[1] - self.current_xlim[0]) / self.axes.bbox.width) * (event.x - self.mouse_press_position[0])
                delta_y = ((self.current_ylim[1] - self.current_ylim[0]) / self.axes.bbox.height) * (event.y - self.mouse_press_position[1])
                self.axes.set_xlim(self.current_xlim[0] - delta_x, self.current_xlim[1] - delta_x)
                self.axes.set_ylim(self.current_ylim[0] - delta_y, self.current_ylim[1] - delta_y)
                self.axes.figure.canvas.draw_idle()
            elif self.selection_rectangle:
                start_x, start_y = self.selection_rectangle_start
                end_x, end_y = event.xdata, event.ydata
                self.selection_rectangle.set_width(abs(end_x - start_x))
                self.selection_rectangle.set_height(abs(end_y - start_y))
                self.selection_rectangle.set_xy((min(start_x, end_x), min(start_y, end_y)))
                self.axes.figure.canvas.draw_idle()

    def handle_scroll_wheel(self, event):
        """Handles scroll wheel events for focal zooming."""
        if event.inaxes != self.axes:
            return
            
        zoom_factor = (1.0 / DEFAULT_ZOOM_FACTOR) if event.button == "up" else DEFAULT_ZOOM_FACTOR
        current_xlim = self.axes.get_xlim()
        current_ylim = self.axes.get_ylim()
        event_xdata, event_ydata = event.xdata, event.ydata
        
        if self.axes.get_xscale() == 'log':
            self.axes.set_xlim(event_xdata * (current_xlim[0] / event_xdata) ** zoom_factor, event_xdata * (current_xlim[1] / event_xdata) ** zoom_factor)
        else:
            self.axes.set_xlim((current_xlim[0] - event_xdata) * zoom_factor + event_xdata, (current_xlim[1] - event_xdata) * zoom_factor + event_xdata)
            
        if self.axes.get_yscale() == 'log':
            self.axes.set_ylim(event_ydata * (current_ylim[0] / event_ydata) ** zoom_factor, event_ydata * (current_ylim[1] / event_ydata) ** zoom_factor)
        else:
            self.axes.set_ylim((current_ylim[0] - event_ydata) * zoom_factor + event_ydata, (current_ylim[1] - event_ydata) * zoom_factor + event_ydata)
            
        self.axes.figure.canvas.draw()
        self._notify_view_change()

    def reset_view(self):
        """Resets the axes view to the initial limits."""
        self.axes.set_xlim(self.initial_xlim)
        self.axes.set_ylim(self.initial_ylim)
        self.axes.figure.canvas.draw()
        self._notify_view_change()

    def _notify_view_change(self):
        """Notifies external observers of a change in axis limits."""
        if self.event_callbacks and "on_view_change" in self.event_callbacks:
            self.event_callbacks["on_view_change"](self.axes.get_xlim(), self.axes.get_ylim())

    def _handle_axis_double_click(self, mouse_x, mouse_y, axes_bbox):
        """Handles double-click events on axis labels to set custom limits."""
        if axes_bbox.x0 <= mouse_x <= axes_bbox.x1:
            if axes_bbox.y0 - AXIS_CLICK_THRESHOLD_PIXELS < mouse_y < axes_bbox.y0:
                self._request_axis_limit('x', 'min')
            elif mouse_y > axes_bbox.y1:
                self._request_axis_limit('y', 'max')
        elif axes_bbox.y0 <= mouse_y <= axes_bbox.y1:
            if axes_bbox.x0 - AXIS_CLICK_THRESHOLD_PIXELS < mouse_x < axes_bbox.x0:
                self._request_axis_limit('y', 'min')
            elif mouse_x > axes_bbox.x1:
                self._request_axis_limit('x', 'max')

    def _request_axis_limit(self, axis_name, limit_side):
        """Opens a dialog to manually set an axis limit."""
        current_limits = self.axes.get_xlim() if axis_name == 'x' else self.axes.get_ylim()
        limit_index = 0 if limit_side == 'min' else 1
        
        new_value = simpledialog.askfloat("Limit", f"{axis_name.upper()} {limit_side}:", initialvalue=current_limits[limit_index])
        
        if new_value is not None:
            if axis_name == 'x':
                self.axes.set_xlim(left=new_value) if limit_side == 'min' else self.axes.set_xlim(right=new_value)
            else:
                self.axes.set_ylim(bottom=new_value) if limit_side == 'min' else self.axes.set_ylim(top=new_value)
            self.axes.figure.canvas.draw_idle()
            self._notify_view_change()

    def _initialize_axis_mode(self, mouse_x, mouse_y, axes_bbox, mouse_button):
        """Sets the active zooming or panning mode based on click location."""
        mode_attribute = 'active_axis_zoom_mode' if mouse_button == LEFT_CLICK else 'active_axis_pan_mode'
        
        if (axes_bbox.x0 <= mouse_x <= axes_bbox.x1) and (axes_bbox.y0 - AXIS_CLICK_THRESHOLD_PIXELS < mouse_y < axes_bbox.y0 or mouse_y > axes_bbox.y1):
            setattr(self, mode_attribute, 'x')
            self.mouse_press_position = (mouse_x, mouse_y)
            self.current_xlim = self.axes.get_xlim()
        elif (axes_bbox.y0 <= mouse_y <= axes_bbox.y1) and (axes_bbox.x0 - AXIS_CLICK_THRESHOLD_PIXELS < mouse_x < axes_bbox.x0 or mouse_x > axes_bbox.x1):
            setattr(self, mode_attribute, 'y')
            self.mouse_press_position = (mouse_x, mouse_y)
            self.current_ylim = self.axes.get_ylim()
