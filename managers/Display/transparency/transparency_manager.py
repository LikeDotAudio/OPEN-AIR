# managers/Display/transparency/transparency_manager.py
import tkinter as tk
from loguru import logger
from PIL import ImageTk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

class TransparencyManager:
    """
    Centralized engine for Industrial Transparency.
    Slices the background procedural patina to blend widgets seamlessly.
    """
    
    @staticmethod
    def cleanup(builder_instance):
        """
        Clears the slicing registry and image references for a builder.
        Call this during tab closure or complete GUI rebuilds.
        """
        if LOCAL_DEBUG: logger.trace(f"TransparencyManager: Cleaning up context for {builder_instance}")
        if hasattr(builder_instance, '_slicing_registry'):
            builder_instance._slicing_registry.clear()
        
        # Force a system garbage collection after a major cleanup
        import gc
        gc.collect()

    @staticmethod
    def apply_transparency(widget, canvas, config, builder_instance):
        """
        Registers a widget for background slicing.
        Gated: Only applies if no background color is explicitly set or if 'transparent' is true.
        """
        if not widget or not builder_instance:
            if LOCAL_DEBUG: logger.warning(f"TransparencyManager: Missing widget or builder_instance. Widget: {widget}, Builder: {builder_instance}")
            return

        # ⚡ DEBUG: Check builder_instance capabilities
        has_registry = hasattr(builder_instance, 'register_for_slicing')
        has_bg = hasattr(builder_instance, 'panel_bg_pil')
        
        # 1. Determine if transparency is appropriate
        # By default, everything is transparent unless it has a solid non-theme color
        
        # Check various common background keys
        bg = config.get("bg_color") or config.get("bg") or config.get("background_color")
        if not bg:
            # Check nested style config
            style = config.get("style", {})
            if isinstance(style, dict):
                bg = style.get("background_color") or style.get("bg_color") or style.get("bg")
        
        # ⚡ VIRTUAL CONTAINER AWARENESS: Structural containers should always be transparent-friendly
        # Use robust type checking for OcaBlocks/Arrays which are implemented as tk.Canvas
        STRUCTURAL_TYPES = ["OcaBlock", "OcaBin", "OcaArray", "OcaCollapsibleBlock", "Block", "Array", "Bin"]
        is_struct_type = any(config.get(k) in STRUCTURAL_TYPES for k in ["type", "widget_type"])
        is_virtual_container = is_struct_type and isinstance(widget, tk.Canvas)
        
        # If it's a standard hex color like #2b2b2b, we assume it's the theme and allow transparency
        # If it's "transparent", "None", or empty, definitely transparent.
        bg_str = str(bg).lower() if bg else ""
        
        # ⚡ THEME AWARENESS: These colors are part of the theme and should be treated as transparent
        THEME_COLORS = ["#2b2b2b", "#3c3f41", "#4e5254", "#1a1a1a", "#000000", "#dcdcdc", "#f0f0f0"]
        is_explicitly_solid = (bg and str(bg).startswith("#") and bg_str not in THEME_COLORS)
        is_explicitly_transparent = (bg_str in ["transparent", "none", "match_theme"]) or (config.get("transparent") is True) or is_virtual_container
        
        if LOCAL_DEBUG: logger.trace(f"TransparencyManager: Applying to {widget}. BG: {bg_str}, Solid: {is_explicitly_solid}, Trans: {is_explicitly_transparent}")

        # Explicit override to DISABLE
        if config.get("transparent") is False:
            if LOCAL_DEBUG: logger.debug(f"TransparencyManager: {widget} explicitly disabled via config.")
            return
            
        # If forced transparent, ignore solid color check
        if is_explicitly_solid and not is_explicitly_transparent:
            if LOCAL_DEBUG: logger.debug(f"TransparencyManager: {widget} skipped due to solid color: {bg_str}")
            return

        # 2. Define slicing logic
        def _perform_slice(source_bg_pil=None, scroll_ref=None, scroll_root_x=None, scroll_root_y=None):
            if not widget.winfo_exists(): return
            
            # If we have a separate canvas for drawing, use it for the slice
            draw_target = canvas if canvas and canvas.winfo_exists() else widget
            
            # Get background source
            source = source_bg_pil or getattr(builder_instance, 'panel_bg_pil', None)
            
            # ⚡ FALLBACK: If no source image, ensure we at least use the theme background
            if not source:
                # 🛡️ SILENCE: If background is explicitly 'none', theme fallback is intended.
                bg_cfg = getattr(builder_instance, 'config_data', {}).get("background")
                if bg_cfg == "none":
                    return 

                # Only warn if we're not currently generating a new background or rebuilding
                # Also skip if we are in early layout (1x1)
                try:
                    w, h = draw_target.winfo_width(), draw_target.winfo_height()
                except:
                    w, h = 0, 0
                    
                is_busy = getattr(builder_instance, '_is_rebuilding', False) or \
                          (getattr(builder_instance, '_bg_task_id', 0) > 0 and getattr(builder_instance, 'panel_bg_pil', None) is None)
                
                if not is_busy and w > 1 and h > 1:
                    # ⚡ SILENCE: Theme fallback is a normal state, not a warning.
                    if LOCAL_DEBUG: logger.trace(f"TransparencyManager: No source image for {widget}. Using theme fallback.")
                
                try:
                    theme_bg = "#2b2b2b" # Default
                    if hasattr(builder_instance, 'theme_colors'):
                        theme_bg = builder_instance.theme_colors.get("bg", theme_bg)
                    
                    if widget.cget("bg") != theme_bg:
                        widget.configure(bg=theme_bg)
                    if canvas and canvas.winfo_exists() and canvas.cget("bg") != theme_bg:
                        canvas.configure(bg=theme_bg)
                except Exception as e: 
                    if LOCAL_DEBUG: logger.error(f"TransparencyManager fallback error: {e}")
                return

            try:
                # ⚡ OPTIMIZATION: Use root coordinates for fast relative calculation
                # Use a small per-event cache to avoid redundant winfo_rootx calls in batch passes
                cache = getattr(builder_instance, '_root_coord_cache', None)
                
                if cache is not None and id(draw_target) in cache:
                    wx, wy = cache[id(draw_target)]
                else:
                    wx, wy = draw_target.winfo_rootx(), draw_target.winfo_rooty()
                    if cache is not None: cache[id(draw_target)] = (wx, wy)
                
                # Use pre-calculated scroll root or look it up
                if scroll_root_x is not None and scroll_root_y is not None:
                    sx, sy = scroll_root_x, scroll_root_y
                else:
                    # Use cache for scroll root too
                    if cache is not None and "scroll_root" in cache:
                        sx, sy = cache["scroll_root"]
                    else:
                        ref = scroll_ref or getattr(builder_instance, 'scroll_frame', None)
                        if not ref: 
                            if LOCAL_DEBUG: logger.trace(f"TransparencyManager: No scroll_frame reference for {widget} in {builder_instance}")
                            return
                        sx, sy = ref.winfo_rootx(), ref.winfo_rooty()
                        if cache is not None: cache["scroll_root"] = (sx, sy)

                rel_x, rel_y = wx - sx, wy - sy
                w, h = draw_target.winfo_width(), draw_target.winfo_height()
                
                # ⚡ OPTIMIZATION: 1x1 is a standard 'pre-layout' state in Tkinter.
                if w <= 1 or h <= 1: 
                    return

                # ⚡ JITTER FILTERING: If coordinates moved by < 2 pixels, and image ID/size is same, ignore.
                # This stops 'shimmering' during subtle parent resizes or scroll jitters.
                last_state = getattr(draw_target, '_last_slice_state', (None, None, 0, 0, 0))
                last_rx, last_ry, last_w, last_h, last_img_id = last_state
                
                if last_img_id == id(source) and w == last_w and h == last_h and last_rx is not None:
                    dx, dy = abs(rel_x - last_rx), abs(rel_y - last_ry)
                    if dx < 2 and dy < 2:
                        if LOCAL_DEBUG: logger.trace(f"TransparencyManager: Slice SKIPPED for {widget} (Jitter Filter). Delta: ({dx}px, {dy}px)")
                        return

                current_state = (rel_x, rel_y, w, h, id(source))
                
                if LOCAL_DEBUG:
                    reason = "Image ID Change" if last_img_id != id(source) else "Coordinate Shift"
                    logger.trace(f"TransparencyManager: Slicing {widget} ({w}x{h}) at ({rel_x}, {rel_y}). Reason: {reason}")

                # Perform the crop
                bw, bh = source.size
                
                # ⚡ ROBUSTNESS: Ensure crop coordinates are within image bounds
                # If widget is partially off-background, we clamp and sample the edge
                x1, y1 = max(0, min(bw - 1, rel_x)), max(0, min(bh - 1, rel_y))
                x2, y2 = max(x1 + 1, min(bw, rel_x + w)), max(y1 + 1, min(bh, rel_y + h))
                
                if x2 > x1 and y2 > y1:
                    try:
                        crop = source.crop((x1, y1, x2, y2))
                        
                        # Update widget flat color (center sample) for safety/containers
                        center_rgb = crop.getpixel(((x2-x1)//2, (y2-y1)//2))
                        hex_bg = '#%02x%02x%02x' % center_rgb[:3]
                        
                        # ⚡ MANDATORY: Update both container and draw target backgrounds
                        if widget.cget("bg") != hex_bg:
                            widget.configure(bg=hex_bg)
                        if draw_target != widget and draw_target.cget("bg") != hex_bg:
                            draw_target.configure(bg=hex_bg)

                        # If it's a canvas, draw the slice
                        if isinstance(draw_target, tk.Canvas):
                            tk_img = ImageTk.PhotoImage(crop)
                            
                            # ⚡ MANDATORY: Keep reference on BOTH to prevent GC and support custom draw methods
                            draw_target.panel_bg_image = tk_img
                            draw_target.panel_bg_pil_slice = crop
                            draw_target.panel_bg_pil = source # ⚡ Full source for masking logic
                            
                            if widget != draw_target:
                                widget.panel_bg_image = tk_img
                                widget.panel_bg_pil_slice = crop
                                widget.panel_bg_pil = source # ⚡ Full source
                                
                            draw_target.delete("panel_bg_slice")
                            draw_target.create_image(0, 0, image=tk_img, anchor="nw", tags="panel_bg_slice")
                            draw_target.tag_lower("panel_bg_slice")
                        
                        draw_target._last_slice_state = current_state
                        
                        # Trigger redraw if widget has custom drawing logic
                        if hasattr(widget, 'render'): widget.render()
                        elif hasattr(widget, '_draw'): widget._draw()

                    except Exception as e:
                        if LOCAL_DEBUG: logger.error(f"TransparencyManager slicing/color error: {e}")
                else:
                    # Silently skip slicing for truly off-screen widgets (common during scrolling/rebuilds)
                    if LOCAL_DEBUG: logger.trace(f"TransparencyManager: Skipping empty crop for {widget} at ({x1},{y1}) to ({x2},{y2}) [BW: {bw}, BH: {bh}]")
                    return
                    
            except Exception as e:
                if LOCAL_DEBUG: logger.exception(f"TransparencyManager: Error slicing {widget}: {e}")

        # 3. Register with builder for synchronized batch reslicing
        if hasattr(builder_instance, 'register_for_slicing'):
            builder_instance.register_for_slicing(_perform_slice)
        else:
            # ⚡ OPTIMIZATION: Suppress noise. If not a DynamicGuiBuilder, transparency 
            # might not be supported or is handled manually.
            if LOCAL_DEBUG: logger.trace(f"TransparencyManager: builder_instance {builder_instance} ({type(builder_instance)}) missing 'register_for_slicing'")
        
        # Also bind to Map to ensure we slice when first visible
        widget.bind("<Map>", lambda e: _perform_slice(), add="+")
