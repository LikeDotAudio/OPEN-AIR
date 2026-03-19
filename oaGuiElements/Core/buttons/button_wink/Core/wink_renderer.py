import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFilter

def _create_rounded_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Helper to draw a rounded rectangle."""
    points = [
        x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y1 + radius, x2, y2 - radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x2 - radius, y2, x1 + radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def draw_circular_mask(canvas, width, height):
    """
    Generates a masking overlay that hides shutters outside the circle.
    Uses the background slice and cuts a hole.
    """
    # ⚡ INDUSTRIAL TRANSPARENCY: Require patina slice for masking
    if not hasattr(canvas, 'panel_bg_pil_slice') or not canvas.panel_bg_pil_slice:
        return None

    # Check cache (Invalidate if dims OR the background object itself changed)
    if (not hasattr(canvas, 'circular_mask_image') or 
        getattr(canvas, 'last_mask_dims', None) != (width, height) or
        getattr(canvas, 'last_mask_bg_id', None) != id(canvas.panel_bg_pil_slice)):
        
        canvas.last_mask_dims = (width, height)
        canvas.last_mask_bg_id = id(canvas.panel_bg_pil_slice)
        
        # 1. High-Quality Rendering (Upscale)
        UPSCALE_FACTOR = 4
        upscale_width, upscale_height = int(width * UPSCALE_FACTOR), int(height * UPSCALE_FACTOR)
        
        # Prepare Background from the correctly positioned slice
        background_pil = canvas.panel_bg_pil_slice.resize((upscale_width, upscale_height), Image.Resampling.LANCZOS).convert("RGBA")

        # 3. Create a mask (Black everywhere, transparent circle in middle)
        MASK_COLOR_OPAQUE = 255
        mask = Image.new("L", (upscale_width, upscale_height), MASK_COLOR_OPAQUE)
        mask_draw = ImageDraw.Draw(mask)
        mask_size = min(upscale_width, upscale_height)
        offset_x, offset_y = (upscale_width - mask_size) / 2, (upscale_height - mask_size) / 2

        # Draw the hole
        MASK_COLOR_TRANSPARENT = 0
        mask_draw.ellipse((offset_x, offset_y, offset_x + mask_size, offset_y + mask_size), fill=MASK_COLOR_TRANSPARENT)

        # 4. Apply mask to the background slice
        background_pil.putalpha(mask)

        # 5. Downscale for smooth anti-aliased edges
        background_pil = background_pil.resize((int(width), int(height)), Image.Resampling.LANCZOS)

        canvas.circular_mask_image = ImageTk.PhotoImage(background_pil)

    # Use item ID to update existing mask instead of creating new ones
    if hasattr(canvas, 'circular_mask_id') and canvas.itemconfig(canvas.circular_mask_id):
        canvas.itemconfig(canvas.circular_mask_id, image=canvas.circular_mask_image)
        return canvas.circular_mask_id
    
    canvas.circular_mask_id = canvas.create_image(0, 0, image=canvas.circular_mask_image, anchor="nw", tags="wink_mask")
    return canvas.circular_mask_id

def draw_rounded_mask(canvas, width, height, radius):
    """
    Generates a masking overlay for rounded corners.
    Uses the background slice and cuts a rounded hole.
    """
    # ⚡ INDUSTRIAL TRANSPARENCY: Require patina slice for masking
    if not hasattr(canvas, 'panel_bg_pil_slice') or not canvas.panel_bg_pil_slice:
        return None

    # Check cache
    if (not hasattr(canvas, 'rounded_mask_image') or 
        getattr(canvas, 'last_rmask_dims', None) != (width, height, radius) or
        getattr(canvas, 'last_rmask_bg_id', None) != id(canvas.panel_bg_pil_slice)):
        
        canvas.last_rmask_dims = (width, height, radius)
        canvas.last_rmask_bg_id = id(canvas.panel_bg_pil_slice)
        
        UPSCALE_FACTOR = 4
        upscale_width, upscale_height = int(width * UPSCALE_FACTOR), int(height * UPSCALE_FACTOR)
        upscale_radius = int(radius * UPSCALE_FACTOR)
        
        # Prepare Background from the correctly positioned slice
        background_pil = canvas.panel_bg_pil_slice.resize((upscale_width, upscale_height), Image.Resampling.LANCZOS).convert("RGBA")
        
        # Create a mask
        MASK_COLOR_OPAQUE = 255
        mask = Image.new("L", (upscale_width, upscale_height), MASK_COLOR_OPAQUE)
        mask_draw = ImageDraw.Draw(mask)
        
        # Draw the rounded hole
        MASK_COLOR_TRANSPARENT = 0
        mask_draw.rounded_rectangle((0, 0, upscale_width, upscale_height), radius=upscale_radius, fill=MASK_COLOR_TRANSPARENT)
        
        background_pil.putalpha(mask)
        background_pil = background_pil.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        canvas.rounded_mask_image = ImageTk.PhotoImage(background_pil)

    if hasattr(canvas, 'rounded_mask_id') and canvas.itemconfig(canvas.rounded_mask_id):
        canvas.itemconfig(canvas.rounded_mask_id, image=canvas.rounded_mask_image)
        return canvas.rounded_mask_id
    
    canvas.rounded_mask_id = canvas.create_image(0, 0, image=canvas.rounded_mask_image, anchor="nw", tags="wink_mask")
    return canvas.rounded_mask_id

def draw_glass_lens(canvas, width, height, shape_type, radius, border_color, border_thickness, state):
    """Draws a blurred glass lens effect over the button, cached on canvas."""
    # Check if we need to regenerate the lens image
    if (not hasattr(canvas, 'glass_lens_image') or 
        getattr(canvas, 'last_lens_dims', None) != (width, height) or
        getattr(canvas, 'last_lens_color', None) != border_color):
        
        canvas.last_lens_dims = (width, height)
        canvas.last_lens_color = border_color
        
        UPSCALE_FACTOR = 2
        upscale_width, upscale_height = int(width * UPSCALE_FACTOR), int(height * UPSCALE_FACTOR)
        upscale_radius = radius * UPSCALE_FACTOR
        
        lens_img = Image.new("RGBA", (upscale_width, upscale_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(lens_img)
        MASK_COLOR_TRANSPARENT = 0
        mask = Image.new("L", (upscale_width, upscale_height), MASK_COLOR_TRANSPARENT)
        mask_draw = ImageDraw.Draw(mask)
        
        RIM_WIDTH_OFFSET = 6
        RIM_WIDTH_DIVISOR = 2
        rim_width = (border_thickness + RIM_WIDTH_OFFSET) / RIM_WIDTH_DIVISOR * UPSCALE_FACTOR
        
        MASK_COLOR_OPAQUE = 255
        RIM_OUTLINE_RGBA = (40, 40, 40, 100)
        GLINT_RGBA = (255, 255, 255, 90)
        
        if shape_type == "round":
            mask_size = min(upscale_width, upscale_height)
            offset_x, offset_y = (upscale_width - mask_size) / 2, (upscale_height - mask_size) / 2
            mask_draw.ellipse((offset_x, offset_y, offset_x + mask_size, offset_y + mask_size), fill=MASK_COLOR_OPAQUE)
            draw.ellipse((offset_x, offset_y, offset_x + mask_size, offset_y + mask_size), outline=RIM_OUTLINE_RGBA, width=int(rim_width))
            
            GLINT_START_ANGLE = 180
            GLINT_EXTENT_ANGLE = 300
            draw.arc((offset_x + 1, offset_y + 1, offset_x + mask_size - 1, offset_y + mask_size - 1), 
                     start=GLINT_START_ANGLE, end=GLINT_EXTENT_ANGLE, fill=GLINT_RGBA, width=int(UPSCALE_FACTOR))
        else:
            mask_draw.rounded_rectangle((0, 0, upscale_width, upscale_height), radius=upscale_radius, fill=MASK_COLOR_OPAQUE)
            draw.rounded_rectangle((0, 0, upscale_width, upscale_height), radius=upscale_radius, outline=RIM_OUTLINE_RGBA, width=int(rim_width))
            
            SIDE_GLINT_RGBA = (255, 255, 255, 60)
            GLINT_PADDING = 2 * UPSCALE_FACTOR
            draw.line((upscale_radius, GLINT_PADDING, upscale_width - upscale_radius, GLINT_PADDING), fill=SIDE_GLINT_RGBA, width=int(UPSCALE_FACTOR))
            draw.line((GLINT_PADDING, upscale_radius, GLINT_PADDING, upscale_height - upscale_radius), fill=SIDE_GLINT_RGBA, width=int(UPSCALE_FACTOR))

        # Glint
        glint_layer = Image.new("RGBA", (upscale_width, upscale_height), (0, 0, 0, 0))
        glint_draw = ImageDraw.Draw(glint_layer)
        
        if shape_type == "round":
            mask_size = min(upscale_width, upscale_height)
            offset_x, offset_y = (upscale_width - mask_size) / 2, (upscale_height - mask_size) / 2
            GLINT_X_SCALE, GLINT_Y_SCALE = 0.05, 0.1
            GLINT_W_SCALE, GLINT_H_SCALE = 0.75, 0.4
            GLINT_FILL_RGBA = (255, 255, 255, 50)
            glint_draw.ellipse((offset_x - mask_size * GLINT_X_SCALE, offset_y - mask_size * GLINT_Y_SCALE, 
                               offset_x + mask_size * GLINT_W_SCALE, offset_y + mask_size * GLINT_H_SCALE), 
                              fill=GLINT_FILL_RGBA)
        else:
            RECT_GLINT_X_SCALE, RECT_GLINT_Y_SCALE = -0.05, -0.1
            RECT_GLINT_W_SCALE, RECT_GLINT_H_SCALE = 0.75, 0.45
            RECT_GLINT_FILL_RGBA = (255, 255, 255, 40)
            glint_draw.ellipse((upscale_width * RECT_GLINT_X_SCALE, upscale_height * RECT_GLINT_Y_SCALE, 
                               upscale_width * RECT_GLINT_W_SCALE, upscale_height * RECT_GLINT_H_SCALE), 
                              fill=RECT_GLINT_FILL_RGBA)
        
        GLINT_BLUR_RADIUS = 5 * UPSCALE_FACTOR
        glint_layer = glint_layer.filter(ImageFilter.GaussianBlur(radius=GLINT_BLUR_RADIUS))
        lens_img.paste(glint_layer, (0, 0), mask=mask)
        
        lens_img = lens_img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        canvas.glass_lens_image = ImageTk.PhotoImage(lens_img)

    return canvas.create_image(0, 0, image=canvas.glass_lens_image, anchor="nw", tags="wink_lens")

def draw_wink_visuals(canvas, state, config, label_text=None):
    """
    ⚡ OPTIMIZED: Redraws the Wink Button visuals using individual item updates.
    Eliminates canvas.delete(ALL) spam.
    """
    width, height = state["dims"]["w"], state["dims"]["h"]
    shape_type, radius = config["shape_type"], config["radius"]
    bg_color, shutter_color = config["bg_color"], config["shutter_color"]
    border_color, border_thickness = config["border_color"], config["border_thickness"]
    
    # 1. Structural initialization (once)
    if not state.get("_initialized"):
        state["_items"] = {}
        # Background
        if hasattr(canvas, 'panel_bg_image'):
            state["_items"]["bg"] = canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw")
        
        # Neon
        if shape_type == "round":
            mask_size = min(width, height)
            offset_x, offset_y = (width - mask_size) / 2, (height - mask_size) / 2
            state["_items"]["neon"] = canvas.create_oval(offset_x, offset_y, offset_x + mask_size, offset_y + mask_size, fill=bg_color, outline="")
        else:
            state["_items"]["neon"] = _create_rounded_rect(canvas, 1, 1, width - 1, height - 1, radius=max(radius, 2), fill=bg_color, outline="")
            
        # Text Inside
        if config["text_inside"]:
            DEFAULT_TEXT_SIZE_RATIO = 0.25
            font_size = config["font_size"] or int(min(width, height) * DEFAULT_TEXT_SIZE_RATIO)
            text_x, anchor = (width / 2, "center")
            TEXT_PADDING_X = 4
            if config["text_align"] in ["left", "w"]: 
                text_x, anchor = TEXT_PADDING_X, "w"
            elif config["text_align"] in ["right", "e"]: 
                text_x, anchor = width - TEXT_PADDING_X, "e"
            state["_items"]["text_in"] = canvas.create_text(text_x, height / 2, text=config["text_inside"], fill=config["text_inside_color"], font=("Arial", font_size, "bold"), anchor=anchor)

        # Shutters
        state["_items"]["shutter_1"] = canvas.create_rectangle(0,0,0,0, fill=shutter_color, outline="")
        state["_items"]["shutter_2"] = canvas.create_rectangle(0,0,0,0, fill=shutter_color, outline="")
        
        # Porthole / Lens
        if config.get("use_glass_lens"):
            state["_items"]["lens"] = draw_glass_lens(canvas, width, height, shape_type, radius, border_color, border_thickness, state)
        else:
            # Standard Border
            if shape_type == "round":
                mask_size = min(width, height)
                offset_x, offset_y = (width - mask_size) / 2, (height - mask_size) / 2
                state["_items"]["border"] = canvas.create_oval(offset_x + border_thickness / 2, offset_y + border_thickness / 2, 
                                                              offset_x + mask_size - border_thickness / 2, offset_y + mask_size - border_thickness / 2, 
                                                              outline=border_color, width=border_thickness)
            else:
                state["_items"]["border"] = _create_rounded_rect(canvas, border_thickness / 2, border_thickness / 2, 
                                                                width - border_thickness / 2, height - border_thickness / 2, 
                                                                radius=radius, outline=border_color, width=border_thickness, fill="")

        # Lock Icon
        LOCK_FONT_SIZE = 10
        state["_items"]["lock"] = canvas.create_text(width - 1, 1, text="🔒", fill="white", font=("Arial", LOCK_FONT_SIZE), anchor="ne", state="hidden")
        
        # External Label
        if label_text and (not config.get("text_inside")):
            label_position = config.get("label_position", "top").lower()
            LABEL_PADDING_XY = 4
            LABEL_SIDE_PADDING = 2
            label_x, label_y, label_anchor = width / 2, LABEL_PADDING_XY, "n"
            if label_position == "bottom": 
                label_y, label_anchor = height - LABEL_PADDING_XY, "s"
            elif label_position == "left": 
                label_x, label_y, label_anchor = LABEL_SIDE_PADDING, height / 2, "w"
            elif label_position == "right": 
                label_x, label_y, label_anchor = width - LABEL_SIDE_PADDING, height / 2, "e"
            
            DEFAULT_LABEL_FONT_SIZE = 10
            label_font = config.get("font_size", DEFAULT_LABEL_FONT_SIZE) or DEFAULT_LABEL_FONT_SIZE
            state["_items"]["label"] = canvas.create_text(label_x, label_y, text=label_text, fill="white", font=("Helvetica", label_font, "bold"), anchor=label_anchor)

        state["_initialized"] = True

    # 2. Lazy/Dynamic Items (Can be created after init)
    # ⚡ MASKING: Draw background over the corners to simulate transparency
    if shape_type == "round":
        mask_id = draw_circular_mask(canvas, width, height)
        if mask_id: state["_items"]["mask"] = mask_id
    elif radius > 0:
        mask_id = draw_rounded_mask(canvas, width, height, radius)
        if mask_id: state["_items"]["mask"] = mask_id

    # 3. Frequent Updates (Physics / Animation)
    base_x, base_y = width / 2, height / 2
    is_horiz = width > height
    gap = (height if is_horiz else width) * state["current_open"]
    
    eff_shutter_col = shutter_color
    HOVER_SHUTTER_COLOR = "#333333"
    HOVER_THRESHOLD = 0.5
    if state["is_hovering"] and shutter_color.lower() in ["black", "#000000"] and state["current_open"] < HOVER_THRESHOLD:
        eff_shutter_col = HOVER_SHUTTER_COLOR

    if is_horiz:
        canvas.coords(state["_items"]["shutter_1"], 0, 0, width, base_y - (gap / 2))
        canvas.coords(state["_items"]["shutter_2"], 0, base_y + (gap / 2), width, height)
    else:
        canvas.coords(state["_items"]["shutter_1"], 0, 0, base_x - (gap / 2), height)
        canvas.coords(state["_items"]["shutter_2"], base_x + (gap / 2), 0, width, height)
    
    canvas.itemconfig(state["_items"]["shutter_1"], fill=eff_shutter_col)
    canvas.itemconfig(state["_items"]["shutter_2"], fill=eff_shutter_col)
    
    # Update Lock
    canvas.itemconfig(state["_items"]["lock"], state="normal" if state["is_locked"] else "hidden")
    
    # Ensure items are correctly stacked
    # Mask must be above shutters but below lens
    if "mask" in state["_items"]: canvas.tag_raise(state["_items"]["mask"], state["_items"]["shutter_2"])
    if "lens" in state["_items"]: canvas.tag_raise(state["_items"]["lens"])
    if "border" in state["_items"]: canvas.tag_raise(state["_items"]["border"])
    if "label" in state["_items"]: canvas.tag_raise(state["_items"]["label"])
