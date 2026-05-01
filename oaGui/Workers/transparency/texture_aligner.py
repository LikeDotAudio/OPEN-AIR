# oaGui/Workers/transparency/background_slicer.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles the pixel-perfect slicing of background images for industrial transparency.

import tkinter as tk
from PIL import ImageTk
from oaLogging.Methods.matrix_gate import matrix_log
from oaStyle.Constants.geometry import DEFAULT_THEME_BACKGROUND, PRE_LAYOUT_DIMENSION_LIMIT
from oaGui.Methods.ui_window_geometry_utils import UIWindowGeometryUtils

class BackgroundSlicer:
    """
    Handles the pixel-perfect slicing of background images for industrial transparency.
    """
    def __init__(self, widget, canvas, builder, widget_name):
        self.widget = widget
        self.canvas = canvas
        self.builder = builder
        self.widget_name = widget_name

    def perform_slice(self, source_bg_pil=None, scroll_ref=None, scroll_root_x=None, scroll_root_y=None):
        if not self.widget.winfo_exists(): return False

        rendering_target = self.canvas if self.canvas and self.canvas.winfo_exists() else self.widget
        
        background_source = source_bg_pil
        container_ref = scroll_ref
        
        if not background_source:
            current_builder = self.builder
            while current_builder:
                background_source = getattr(current_builder, 'panel_bg_pil', None)
                if background_source:
                    container_ref = getattr(current_builder, 'scroll_frame', None)
                    break
                
                parent_builder = getattr(current_builder, 'parent_builder', None)
                if not parent_builder:
                    parent_builder = UIWindowGeometryUtils.find_parent_builder(current_builder)
                current_builder = parent_builder

        if not background_source or not container_ref:
            background_config = getattr(self.builder, 'config_data', {}).get("background")
            app_inst = getattr(self.builder, 'app_instance', None)
            show_bg_toggle = getattr(app_inst, 'show_background_var', None)
            if show_bg_toggle and not show_bg_toggle.get(): background_config = "none"
            if background_config == "none": return False

            theme_background = DEFAULT_THEME_BACKGROUND
            if hasattr(self.builder, 'theme_colors'):
                theme_background = self.builder.theme_colors.get("bg", theme_background)

            try:
                if self.widget.winfo_exists() and self.widget.cget("bg") != theme_background:
                    self.widget.configure(bg=theme_background)
                if self.canvas and self.canvas.winfo_exists() and self.canvas.cget("bg") != theme_background:
                    self.canvas.configure(bg=theme_background)
            except tk.TclError: pass
            return False

        container_ref = scroll_ref or getattr(self.builder, 'scroll_frame', None)
        if not container_ref or not container_ref.winfo_exists(): return False

        relative_x, relative_y = UIWindowGeometryUtils.get_relative_pos(rendering_target, container_ref)
        current_width = rendering_target.winfo_width()
        current_height = rendering_target.winfo_height()

        if current_width <= 1: current_width = rendering_target.winfo_reqwidth()
        if current_height <= 1: current_height = rendering_target.winfo_reqheight()

        if current_width <= PRE_LAYOUT_DIMENSION_LIMIT or current_height <= PRE_LAYOUT_DIMENSION_LIMIT:
            return False

        previous_state = getattr(rendering_target, '_last_slice_state', (None, None, 0, 0, 0))
        last_rel_x, last_rel_y, last_width, last_height, last_image_id = previous_state

        if last_image_id == id(background_source) and current_width == last_width and current_height == last_height and last_rel_x == relative_x and last_rel_y == relative_y:
            return False

        current_slice_state = (relative_x, relative_y, current_width, current_height, id(background_source))
        source_width, source_height = background_source.size

        crop_x1 = max(0, min(source_width - 1, relative_x))
        crop_y1 = max(0, min(source_height - 1, relative_y))
        crop_x2 = max(crop_x1 + 1, min(source_width, relative_x + current_width))
        crop_y2 = max(crop_y1 + 1, min(source_height, relative_y + current_height))

        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
            try:
                image_slice = background_source.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                pixel_val = image_slice.getpixel((0, 0)) 

                if isinstance(pixel_val, tuple):
                    hex_background_color = '#%02x%02x%02x' % pixel_val[:3]
                else:
                    hex_background_color = '#%02x%02x%02x' % (pixel_val, pixel_val, pixel_val)

                if self.widget.winfo_exists(): self.widget.configure(bg=hex_background_color)
                if rendering_target != self.widget and rendering_target.winfo_exists():
                    rendering_target.configure(bg=hex_background_color)

                if isinstance(rendering_target, tk.Canvas) and rendering_target.winfo_exists():
                    tkinter_image = ImageTk.PhotoImage(image_slice)
                    rendering_target.panel_bg_image = tkinter_image
                    rendering_target.delete("panel_bg_slice")
                    rendering_target.create_image(0, 0, image=tkinter_image, anchor="nw", tags="panel_bg_slice")
                    rendering_target.tag_lower("panel_bg_slice")

                rendering_target._last_slice_state = current_slice_state
                if hasattr(self.widget, 'render'): self.widget.render()
                return True
            except Exception as e:
                matrix_log("ui", "transparency", "perform_slice", f"Slice failed for {self.widget_name}: {e}", "DEBUG")
                return False
        return False
