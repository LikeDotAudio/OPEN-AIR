# transparency/transparency.py
# Centralized engine for Industrial Transparency.

import tkinter as tk

from PIL import ImageTk

from oaLogging.Methods.matrix_gate import matrix_log
from oaStyle.Constants.geometry import (
    DEFAULT_THEME_BACKGROUND,
    PRE_LAYOUT_DIMENSION_LIMIT,
    STRUCTURAL_WIDGET_TYPES,
    THEME_BACKGROUND_COLORS,
)


class TransparencyConfig:
    @staticmethod
    def parse_configuration(configuration, widget):
        background_color = configuration.get("bg_color") or configuration.get("bg") or configuration.get("background_color")
        if not background_color:
            style_settings = configuration.get("style", {})
            if isinstance(style_settings, dict):
                background_color = style_settings.get("background_color") or style_settings.get("bg_color") or style_settings.get("bg")

        is_structural_type = any(configuration.get(key) in STRUCTURAL_WIDGET_TYPES for key in ["type", "widget_type"])
        is_virtual_container = is_structural_type and isinstance(widget, tk.Canvas)

        background_string = str(background_color).lower() if background_color else ""

        # Keywords that explicitly signal transparency
        trans_keywords = ["transparent", "none", "match_theme"]

        is_explicitly_solid = (background_color and
                               background_string not in THEME_BACKGROUND_COLORS and
                               background_string not in trans_keywords)

        is_explicitly_transparent = (background_string in trans_keywords) or \
                                    (configuration.get("transparent") is True) or \
                                    is_virtual_container or \
                                    is_structural_type

        return background_string, is_explicitly_solid, is_explicitly_transparent

class BackgroundSlicer:
    def __init__(self, widget, canvas, builder, widget_name):
        self.widget = widget
        self.canvas = canvas
        self.builder = builder
        self.widget_name = widget_name

    def perform_slice(self, source_bg_pil=None, scroll_ref=None, scroll_root_x=None, scroll_root_y=None):
        if not self.widget.winfo_exists(): return False

        rendering_target = self.canvas if self.canvas and self.canvas.winfo_exists() else self.widget
        background_source = source_bg_pil or getattr(self.builder, 'panel_bg_pil', None)

        if not background_source:
            # [ ... rest of the existing fallback logic remains mostly same but using the same improved color check ...]
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

        # ⚡ PIXEL-PERFECT COORDINATE CALCULATION
        # winfo_rootx/y returns 0 for unmapped widgets. We traverse up to the scroll_frame
        # to calculate absolute offsets that are stable during the build phase.

        container_ref = scroll_ref or getattr(self.builder, 'scroll_frame', None)
        if not container_ref or not container_ref.winfo_exists(): return False

        def get_relative_pos(w, root):
            curr = w
            rx, ry = 0, 0
            while curr and curr != root:
                rx += curr.winfo_x()
                ry += curr.winfo_y()
                parent_path = curr.winfo_parent()
                if not parent_path: break
                curr = curr.nametowidget(parent_path)
            return rx, ry

        relative_x, relative_y = get_relative_pos(rendering_target, container_ref)
        current_width = rendering_target.winfo_width()
        current_height = rendering_target.winfo_height()

        # If dimensions are 1x1 or less, we use requested size as a hint for early slicing
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

        # ⚡ CLAMPING: Ensure we stay within the source image bounds
        crop_x1 = max(0, min(source_width - 1, relative_x))
        crop_y1 = max(0, min(source_height - 1, relative_y))
        crop_x2 = max(crop_x1 + 1, min(source_width, relative_x + current_width))
        crop_y2 = max(crop_y1 + 1, min(source_height, relative_y + current_height))

        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
            try:
                image_slice = background_source.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                pixel_val = image_slice.getpixel((0, 0)) # Sample top-left for bg color fallback

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

class TransparencyManager:
    @staticmethod
    def cleanup(builder):
        if hasattr(builder, '_slicing_registry'):
            builder._slicing_registry.clear()
        import gc
        gc.collect()

    @staticmethod
    def apply_transparency(widget, canvas, configuration, builder):
        if not widget or not builder: return
        # ⚡ HARDENING: If builder is a widget, it's a legacy call or mis-injection.
        # We must avoid treating it as a builder object to prevent cget(0) errors.
        if isinstance(builder, tk.Widget):
            return

        # ⚡ RENDER TIER BYPASS: Skip transparency registration in Fast/Ghost modes
        render_tier = getattr(builder, '_render_tier', 'high_res')
        if render_tier in ['fast', 'ghost']:
            # Set default theme background for safety
            theme_background = DEFAULT_THEME_BACKGROUND
            if hasattr(builder, 'theme_colors'):
                theme_background = builder.theme_colors.get("bg", theme_background)

            try:
                if widget.winfo_exists(): widget.configure(bg=theme_background)
                if canvas and canvas.winfo_exists(): canvas.configure(bg=theme_background)
            except: pass
            return

        widget_name = getattr(widget, 'path', type(widget).__name__)

        try:
            TransparencyManager._register_widget_for_slicing(widget, canvas, configuration, builder, widget_name)
        except Exception as e:
            TransparencyManager._handle_registration_failure(widget, widget_name, e)

    @staticmethod
    def _register_widget_for_slicing(widget, canvas, configuration, builder, widget_name):
        bg_string, is_solid, is_transparent = TransparencyConfig.parse_configuration(configuration, widget)

        # ⚡ OPTIMIZATION: Only register if transparency is explicitly requested or expected.
        # Avoids redundant slicing for standard widgets with default backgrounds.
        if not is_transparent or (is_solid and not is_transparent):
            return

        slicer = BackgroundSlicer(widget, canvas, builder, widget_name)

        widget._perform_background_slice = slicer.perform_slice

        if hasattr(builder, 'register_for_slicing'):
            builder.register_for_slicing(slicer.perform_slice)
        widget.bind("<Map>", lambda event: slicer.perform_slice(), add="+")

    @staticmethod
    def _handle_registration_failure(widget, widget_name, e):
        matrix_log("ui", "transparency", "apply_transparency", f"❌ TransparencyManager: Failed to apply to {widget_name}: {e}", "ERROR")
        if widget.winfo_exists() and isinstance(widget, tk.Canvas):
            widget.create_text(10, 10, text=f"Transparency Error: {e}", fill="red", anchor="nw")
