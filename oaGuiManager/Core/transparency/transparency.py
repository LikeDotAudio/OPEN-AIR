# transparency/transparency.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from loguru import logger
from PIL import ImageTk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file

# Dimension and Coordinate Constants
MIN_WIDGET_DIMENSION = 1
PRE_LAYOUT_DIMENSION_LIMIT = 1
JITTER_THRESHOLD_PIXELS = 5
CENTER_SAMPLE_DIVISOR = 2

# Structural and Theme Constants
STRUCTURAL_WIDGET_TYPES = ["OcaBlock", "OcaBin", "OcaArray", "OcaCollapsibleBlock", "Block", "Array", "Bin"]
THEME_BACKGROUND_COLORS = ["#2b2b2b", "#3c3f41", "#4e5254", "#1a1a1a", "#000000", "#dcdcdc", "#f0f0f0"]
DEFAULT_THEME_BACKGROUND = "#2b2b2b"

class TransparencyManager:
    """
    Centralized engine for Industrial Transparency.
    Slices the background procedural patina to blend widgets seamlessly.
    """
    
    @staticmethod
    def cleanup(builder):
        """
        Clears the slicing registry and image references for a builder.
        Call this during tab closure or complete GUI rebuilds.
        """
        if LOCAL_DEBUG: 
            logger.trace(f"TransparencyManager: Cleaning up context for {builder}")
        
        if hasattr(builder, '_slicing_registry'):
            builder._slicing_registry.clear()
        
        # Force a system garbage collection after a major cleanup
        import gc
        gc.collect()

    @staticmethod
    def apply_transparency(widget, canvas, configuration, builder):
        """
        Registers a widget for background slicing.
        Gated: Only applies if no background color is explicitly set or if 'transparent' is true.
        """
        if not widget or not builder:
            if LOCAL_DEBUG: 
                logger.warning(f"TransparencyManager: Missing widget or builder. Widget: {widget}, Builder: {builder}")
            return

        try:
            # 1. Determine if transparency is appropriate
            # Check various common background keys
            background_color = configuration.get("bg_color") or configuration.get("bg") or configuration.get("background_color")
            if not background_color:
                # Check nested style configuration
                style_settings = configuration.get("style", {})
                if isinstance(style_settings, dict):
                    background_color = style_settings.get("background_color") or style_settings.get("bg_color") or style_settings.get("bg")
            
            # Structural containers should always be transparent-friendly
            is_structural_type = any(configuration.get(key) in STRUCTURAL_WIDGET_TYPES for key in ["type", "widget_type"])
            is_virtual_container = is_structural_type and isinstance(widget, tk.Canvas)
            
            background_string = str(background_color).lower() if background_color else ""

            # Theme awareness: treat certain colors as transparent
            is_explicitly_solid = (background_color and str(background_color).startswith("#") and background_string not in THEME_BACKGROUND_COLORS)
            
            # Base transparency check
            is_explicitly_transparent = (background_string in ["transparent", "none", "match_theme"]) or \
                                        (configuration.get("transparent") is True) or \
                                        is_virtual_container or \
                                        is_structural_type
            
            widget_name = getattr(widget, 'path', type(widget).__name__)
            if LOCAL_DEBUG: 
                logger.trace(f"TransparencyManager: Applying to {widget_name}. BG: {background_string}, Solid: {is_explicitly_solid}, Trans: {is_explicitly_transparent}")

            # Explicit override to DISABLE
            if configuration.get("transparent") is False:
                if LOCAL_DEBUG: 
                    logger.debug(f"TransparencyManager: {widget_name} explicitly disabled via configuration.")
                return
                
            # If forced transparent, ignore solid color check
            if is_explicitly_solid and not is_explicitly_transparent:
                if LOCAL_DEBUG: 
                    logger.debug(f"TransparencyManager: {widget_name} skipped due to solid color: {background_string}")
                return

            # 2. Define slicing logic
            def _perform_background_slice(source_bg_pil=None, scroll_ref=None, scroll_root_x=None, scroll_root_y=None):
                if not widget.winfo_exists(): 
                    return
                
                # If we have a separate canvas for drawing, use it for the slice
                rendering_target = canvas if canvas and canvas.winfo_exists() else widget
                
                # Get background source image
                background_source = source_bg_pil or getattr(builder, 'panel_bg_pil', None)
                
                # Fallback: if no source image, ensure we at least use the theme background
                if not background_source:
                    background_config = getattr(builder, 'config_data', {}).get("background")
                    if background_config == "none":
                        return 

                    target_width, target_height = 0, 0
                    if rendering_target.winfo_exists():
                        target_width = rendering_target.winfo_width()
                        target_height = rendering_target.winfo_height()
                        
                    is_builder_busy = getattr(builder, '_is_rebuilding', False) or \
                                      (getattr(builder, '_bg_task_id', 0) > 0 and getattr(builder, 'panel_bg_pil', None) is None)
                    
                    if not is_builder_busy and target_width > PRE_LAYOUT_DIMENSION_LIMIT and target_height > PRE_LAYOUT_DIMENSION_LIMIT:
                        if LOCAL_DEBUG: 
                            logger.trace(f"TransparencyManager: No source image for {widget_name}. Using theme fallback.")
                    
                    theme_background = DEFAULT_THEME_BACKGROUND
                    if hasattr(builder, 'theme_colors'):
                        theme_background = builder.theme_colors.get("bg", theme_background)
                    
                    try:
                        if widget.winfo_exists() and widget.cget("bg") != theme_background:
                            widget.configure(bg=theme_background)
                    except tk.TclError:
                        pass # Widget doesn't support 'bg' option (e.g. ttk)

                    try:
                        if canvas and canvas.winfo_exists() and canvas.cget("bg") != theme_background:
                            canvas.configure(bg=theme_background)
                    except tk.TclError:
                        pass
                    return

                # Use root coordinates for fast relative calculation
                coord_cache = getattr(builder, '_root_coord_cache', None)
                
                widget_root_x, widget_root_y = 0, 0
                if rendering_target.winfo_exists():
                    if coord_cache is not None and id(rendering_target) in coord_cache:
                        widget_root_x, widget_root_y = coord_cache[id(rendering_target)]
                    else:
                        widget_root_x = rendering_target.winfo_rootx()
                        widget_root_y = rendering_target.winfo_rooty()
                        if coord_cache is not None: 
                            coord_cache[id(rendering_target)] = (widget_root_x, widget_root_y)
                else:
                    return
                
                # Use pre-calculated scroll root or look it up
                scroll_x, scroll_y = 0, 0
                if scroll_root_x is not None and scroll_root_y is not None:
                    scroll_x, scroll_y = scroll_root_x, scroll_root_y
                else:
                    if coord_cache is not None and "scroll_root" in coord_cache:
                        scroll_x, scroll_y = coord_cache["scroll_root"]
                    else:
                        container_ref = scroll_ref or getattr(builder, 'scroll_frame', None)
                        if not container_ref or not container_ref.winfo_exists(): 
                            if LOCAL_DEBUG: 
                                logger.trace(f"TransparencyManager: No scroll_frame reference for {widget_name} in {builder}")
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

                # Jitter filtering to avoid redundant updates
                previous_state = getattr(rendering_target, '_last_slice_state', (None, None, 0, 0, 0))
                last_rel_x, last_rel_y, last_width, last_height, last_image_id = previous_state
                
                if last_image_id == id(background_source) and current_width == last_width and current_height == last_height and last_rel_x is not None:
                    delta_x = abs(relative_x - last_rel_x)
                    delta_y = abs(relative_y - last_rel_y)
                    if delta_x < JITTER_THRESHOLD_PIXELS and delta_y < JITTER_THRESHOLD_PIXELS:
                        if LOCAL_DEBUG: 
                            logger.trace(f"TransparencyManager: Slice SKIPPED for {widget_name} (Jitter Filter). Delta: ({delta_x}px, {delta_y}px)")
                        return

                current_slice_state = (relative_x, relative_y, current_width, current_height, id(background_source))
                
                # Perform the crop
                source_width, source_height = background_source.size
                
                # Robustness: Ensure crop coordinates are within image bounds
                crop_x1 = max(0, min(source_width - 1, relative_x))
                crop_y1 = max(0, min(source_height - 1, relative_y))
                crop_x2 = max(crop_x1 + 1, min(source_width, relative_x + current_width))
                crop_y2 = max(crop_y1 + 1, min(source_height, relative_y + current_height))
                
                if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                    image_slice = background_source.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                    
                    # Update widget flat color for safety
                    center_color_rgb = image_slice.getpixel(((crop_x2 - crop_x1) // CENTER_SAMPLE_DIVISOR, (crop_y2 - crop_y1) // CENTER_SAMPLE_DIVISOR))
                    hex_background_color = '#%02x%02x%02x' % center_color_rgb[:3]
                    
                    try:
                        if widget.winfo_exists() and widget.cget("bg") != hex_background_color:
                            widget.configure(bg=hex_background_color)
                    except tk.TclError:
                        pass
                        
                    try:
                        if rendering_target != widget and rendering_target.winfo_exists() and rendering_target.cget("bg") != hex_background_color:
                            rendering_target.configure(bg=hex_background_color)
                    except tk.TclError:
                        pass

                    # If it's a canvas, draw the slice
                    if isinstance(rendering_target, tk.Canvas) and rendering_target.winfo_exists():
                        tkinter_image = ImageTk.PhotoImage(image_slice)
                        
                        rendering_target.panel_bg_image = tkinter_image
                        rendering_target.panel_bg_pil_slice = image_slice
                        rendering_target.panel_bg_pil = background_source
                        
                        if widget != rendering_target and widget.winfo_exists():
                            widget.panel_bg_image = tkinter_image
                            widget.panel_bg_pil_slice = image_slice
                            widget.panel_bg_pil = background_source
                            
                        rendering_target.delete("panel_bg_slice")
                        rendering_target.create_image(0, 0, image=tkinter_image, anchor="nw", tags="panel_bg_slice")
                        rendering_target.tag_lower("panel_bg_slice")
                    
                    rendering_target._last_slice_state = current_slice_state
                    
                    # Trigger redraw if widget has custom drawing logic
                    if hasattr(widget, 'render'): 
                        widget.render()
                    elif hasattr(widget, '_draw'): 
                        widget._draw()
                else:
                    if LOCAL_DEBUG: 
                        logger.trace(f"TransparencyManager: Skipping empty crop for {widget_name} at ({crop_x1},{crop_y1}) to ({crop_x2},{crop_y2})")
                    return

            # 3. Register with builder for synchronized batch reslicing
            widget._perform_background_slice = _perform_background_slice
            
            if hasattr(builder, 'register_for_slicing'):
                builder.register_for_slicing(_perform_background_slice)
            
            # Ensure we slice when first visible
            widget.bind("<Map>", lambda event: _perform_background_slice(), add="+")
        except Exception as e:
            logger.exception(f"❌ TransparencyManager: Failed to apply to {widget_name}: {e}")
            # Fallback: display error on screen if possible
            if widget.winfo_exists() and isinstance(widget, tk.Canvas):
                widget.create_text(10, 10, text=f"Transparency Error: {e}", fill="red", anchor="nw")
