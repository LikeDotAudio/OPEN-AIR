# transparency/transparency.py
# Centralized engine for Industrial Transparency.

import tkinter as tk
from loguru import logger
from PIL import ImageTk
from oaLogging.Methods.matrix_gate import matrix_log

# Constants
MIN_WIDGET_DIMENSION = 1
PRE_LAYOUT_DIMENSION_LIMIT = 1
JITTER_THRESHOLD_PIXELS = 5
CENTER_SAMPLE_DIVISOR = 2
STRUCTURAL_WIDGET_TYPES = ["OcaBlock", "OcaBin", "OcaArray", "OcaCollapsibleBlock", "Block", "Array", "Bin"]
THEME_BACKGROUND_COLORS = ["#2b2b2b", "#3c3f41", "#4e5254", "#1a1a1a", "#000000", "#dcdcdc", "#f0f0f0"]
DEFAULT_THEME_BACKGROUND = "#2b2b2b"

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
        is_explicitly_solid = (background_color and str(background_color).startswith("#") and background_string not in THEME_BACKGROUND_COLORS)
        
        is_explicitly_transparent = (background_string in ["transparent", "none", "match_theme"]) or \
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
        if not self.widget.winfo_exists(): return
        
        rendering_target = self.canvas if self.canvas and self.canvas.winfo_exists() else self.widget
        background_source = source_bg_pil or getattr(self.builder, 'panel_bg_pil', None)
        
        if not background_source:
            background_config = getattr(self.builder, 'config_data', {}).get("background")
            if background_config == "none": return 

            target_width, target_height = 0, 0
            if rendering_target.winfo_exists():
                target_width = rendering_target.winfo_width()
                target_height = rendering_target.winfo_height()
                
            is_builder_busy = getattr(self.builder, '_is_rebuilding', False) or \
                              (getattr(self.builder, '_bg_task_id', 0) > 0 and getattr(self.builder, 'panel_bg_pil', None) is None)
            
            if not is_builder_busy and target_width > PRE_LAYOUT_DIMENSION_LIMIT and target_height > PRE_LAYOUT_DIMENSION_LIMIT:
                matrix_log("ui", "transparency", "perform_slice", f"TransparencyManager: No source image for {self.widget_name}. Using theme fallback.", "TRACE")
            
            theme_background = DEFAULT_THEME_BACKGROUND
            if hasattr(self.builder, 'theme_colors'):
                theme_background = self.builder.theme_colors.get("bg", theme_background)
            
            try:
                if self.widget.winfo_exists() and self.widget.cget("bg") != theme_background:
                    self.widget.configure(bg=theme_background)
            except tk.TclError: pass

            try:
                if self.canvas and self.canvas.winfo_exists() and self.canvas.cget("bg") != theme_background:
                    self.canvas.configure(bg=theme_background)
            except tk.TclError: pass
            return

        coord_cache = getattr(self.builder, '_root_coord_cache', None)
        
        widget_root_x, widget_root_y = 0, 0
        if rendering_target.winfo_exists():
            if coord_cache is not None and id(rendering_target) in coord_cache:
                widget_root_x, widget_root_y = coord_cache[id(rendering_target)]
            else:
                widget_root_x = rendering_target.winfo_rootx()
                widget_root_y = rendering_target.winfo_rooty()
                if coord_cache is not None: 
                    coord_cache[id(rendering_target)] = (widget_root_x, widget_root_y)
        else: return
        
        scroll_x, scroll_y = 0, 0
        if scroll_root_x is not None and scroll_root_y is not None:
            scroll_x, scroll_y = scroll_root_x, scroll_root_y
        else:
            if coord_cache is not None and "scroll_root" in coord_cache:
                scroll_x, scroll_y = coord_cache["scroll_root"]
            else:
                container_ref = scroll_ref or getattr(self.builder, 'scroll_frame', None)
                if not container_ref or not container_ref.winfo_exists(): 
                    return
                scroll_x = container_ref.winfo_rootx()
                scroll_y = container_ref.winfo_rooty()
                if coord_cache is not None: 
                    coord_cache["scroll_root"] = (scroll_x, scroll_y)

        relative_x, relative_y = widget_root_x - scroll_x, widget_root_y - scroll_y
        current_width = rendering_target.winfo_width()
        current_height = rendering_target.winfo_height()
        
        if current_width <= PRE_LAYOUT_DIMENSION_LIMIT or current_height <= PRE_LAYOUT_DIMENSION_LIMIT: 
            return

        previous_state = getattr(rendering_target, '_last_slice_state', (None, None, 0, 0, 0))
        last_rel_x, last_rel_y, last_width, last_height, last_image_id = previous_state
        
        if last_image_id == id(background_source) and current_width == last_width and current_height == last_height and last_rel_x is not None:
            delta_x = abs(relative_x - last_rel_x)
            delta_y = abs(relative_y - last_rel_y)
            if delta_x < JITTER_THRESHOLD_PIXELS and delta_y < JITTER_THRESHOLD_PIXELS:
                return

        current_slice_state = (relative_x, relative_y, current_width, current_height, id(background_source))
        source_width, source_height = background_source.size
        
        crop_x1 = max(0, min(source_width - 1, relative_x))
        crop_y1 = max(0, min(source_height - 1, relative_y))
        crop_x2 = max(crop_x1 + 1, min(source_width, relative_x + current_width))
        crop_y2 = max(crop_y1 + 1, min(source_height, relative_y + current_height))
        
        if crop_x2 > crop_x1 and crop_y2 > crop_y1:
            image_slice = background_source.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            center_color_rgb = image_slice.getpixel(((crop_x2 - crop_x1) // CENTER_SAMPLE_DIVISOR, (crop_y2 - crop_y1) // CENTER_SAMPLE_DIVISOR))
            hex_background_color = '#%02x%02x%02x' % center_color_rgb[:3]
            
            try:
                if self.widget.winfo_exists() and self.widget.cget("bg") != hex_background_color:
                    self.widget.configure(bg=hex_background_color)
            except tk.TclError: pass
                
            try:
                if rendering_target != self.widget and rendering_target.winfo_exists() and rendering_target.cget("bg") != hex_background_color:
                    rendering_target.configure(bg=hex_background_color)
            except tk.TclError: pass

            if isinstance(rendering_target, tk.Canvas) and rendering_target.winfo_exists():
                tkinter_image = ImageTk.PhotoImage(image_slice)
                rendering_target.panel_bg_image = tkinter_image
                rendering_target.panel_bg_pil_slice = image_slice
                rendering_target.panel_bg_pil = background_source
                
                if self.widget != rendering_target and self.widget.winfo_exists():
                    self.widget.panel_bg_image = tkinter_image
                    self.widget.panel_bg_pil_slice = image_slice
                    self.widget.panel_bg_pil = background_source
                    
                rendering_target.delete("panel_bg_slice")
                rendering_target.create_image(0, 0, image=tkinter_image, anchor="nw", tags="panel_bg_slice")
                rendering_target.tag_lower("panel_bg_slice")
            
            rendering_target._last_slice_state = current_slice_state
            if hasattr(self.widget, 'render'): self.widget.render()
            elif hasattr(self.widget, '_draw'): self.widget._draw()

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
        widget_name = getattr(widget, 'path', type(widget).__name__)
        
        try:
            TransparencyManager._register_widget_for_slicing(widget, canvas, configuration, builder, widget_name)
        except Exception as e:
            TransparencyManager._handle_registration_failure(widget, widget_name, e)

    @staticmethod
    def _register_widget_for_slicing(widget, canvas, configuration, builder, widget_name):
        bg_string, is_solid, is_transparent = TransparencyConfig.parse_configuration(configuration, widget)

        if configuration.get("transparent") is False or (is_solid and not is_transparent):
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
