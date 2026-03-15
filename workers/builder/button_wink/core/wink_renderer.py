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
        upscale = 4
        uw, uh = int(width * upscale), int(height * upscale)
        
        # 2. Prepare Background from the correctly positioned slice
        bg_pil = canvas.panel_bg_pil_slice.resize((uw, uh), Image.Resampling.LANCZOS).convert("RGBA")
        
        # 3. Create a mask (Black everywhere, transparent circle in middle)
        mask = Image.new("L", (uw, uh), 255)
        m_draw = ImageDraw.Draw(mask)
        size = min(uw, uh)
        ox, oy = (uw-size)/2, (uh-size)/2
        # Draw the hole
        m_draw.ellipse((ox, oy, ox+size, oy+size), fill=0)
        
        # 4. Apply mask to the background slice
        bg_pil.putalpha(mask)
        
        # 5. Downscale for smooth anti-aliased edges
        bg_pil = bg_pil.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        
        canvas.circular_mask_image = ImageTk.PhotoImage(bg_pil)

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
        
        upscale = 4
        uw, uh, ur = int(width * upscale), int(height * upscale), int(radius * upscale)
        
        # Prepare Background from the correctly positioned slice
        bg_pil = canvas.panel_bg_pil_slice.resize((uw, uh), Image.Resampling.LANCZOS).convert("RGBA")
        
        # Create a mask
        mask = Image.new("L", (uw, uh), 255)
        m_draw = ImageDraw.Draw(mask)
        # Draw the rounded hole
        m_draw.rounded_rectangle((0, 0, uw, uh), radius=ur, fill=0)
        
        bg_pil.putalpha(mask)
        bg_pil = bg_pil.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        canvas.rounded_mask_image = ImageTk.PhotoImage(bg_pil)

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
        
        upscale = 2
        uw, uh = int(width * upscale), int(height * upscale)
        ur = radius * upscale
        
        lens_img = Image.new("RGBA", (uw, uh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(lens_img)
        mask = Image.new("L", (uw, uh), 0)
        m_draw = ImageDraw.Draw(mask)
        
        rim_width = (border_thickness + 6) / 2 * upscale
        if shape_type == "round":
            size = min(uw, uh)
            ox, oy = (uw-size)/2, (uh-size)/2
            m_draw.ellipse((ox, oy, ox+size, oy+size), fill=255)
            draw.ellipse((ox, oy, ox+size, oy+size), outline=(40, 40, 40, 100), width=int(rim_width))
            draw.arc((ox+1, oy+1, ox+size-1, oy+size-1), start=180, end=300, fill=(255, 255, 255, 90), width=int(upscale))
        else:
            m_draw.rounded_rectangle((0, 0, uw, uh), radius=ur, fill=255)
            draw.rounded_rectangle((0, 0, uw, uh), radius=ur, outline=(40, 40, 40, 100), width=int(rim_width))
            draw.line((ur, 2*upscale, uw-ur, 2*upscale), fill=(255, 255, 255, 60), width=int(upscale))
            draw.line((2*upscale, ur, 2*upscale, uh-ur), fill=(255, 255, 255, 60), width=int(upscale))

        # Glint
        glint_layer = Image.new("RGBA", (uw, uh), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glint_layer)
        if shape_type == "round":
            size = min(uw, uh)
            ox, oy = (uw-size)/2, (uh-size)/2
            g_draw.ellipse((ox-size*0.05, oy-size*0.1, ox+size*0.75, oy+size*0.4), fill=(255, 255, 255, 50))
        else:
            g_draw.ellipse((-uw*0.05, -uh*0.1, uw*0.75, uh*0.45), fill=(255, 255, 255, 40))
        
        glint_layer = glint_layer.filter(ImageFilter.GaussianBlur(radius=5*upscale))
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
            size = min(width, height)
            ox, oy = (width-size)/2, (height-size)/2
            state["_items"]["neon"] = canvas.create_oval(ox, oy, ox+size, oy+size, fill=bg_color, outline="")
        else:
            state["_items"]["neon"] = _create_rounded_rect(canvas, 1, 1, width-1, height-1, radius=max(radius, 2), fill=bg_color, outline="")
            
        # Text Inside
        if config["text_inside"]:
            f_size = config["font_size"] or int(min(width, height) * 0.25)
            tx, anchor = (width/2, "center")
            if config["text_align"] in ["left", "w"]: tx, anchor = 4, "w"
            elif config["text_align"] in ["right", "e"]: tx, anchor = width-4, "e"
            state["_items"]["text_in"] = canvas.create_text(tx, height/2, text=config["text_inside"], fill=config["text_inside_color"], font=("Arial", f_size, "bold"), anchor=anchor)

        # Shutters
        state["_items"]["s1"] = canvas.create_rectangle(0,0,0,0, fill=shutter_color, outline="")
        state["_items"]["s2"] = canvas.create_rectangle(0,0,0,0, fill=shutter_color, outline="")
        
        # Porthole / Lens
        if config.get("use_glass_lens"):
            state["_items"]["lens"] = draw_glass_lens(canvas, width, height, shape_type, radius, border_color, border_thickness, state)
        else:
            # Standard Border
            if shape_type == "round":
                size = min(width, height)
                ox, oy = (width-size)/2, (height-size)/2
                state["_items"]["border"] = canvas.create_oval(ox+border_thickness/2, oy+border_thickness/2, ox+size-border_thickness/2, oy+size-border_thickness/2, outline=border_color, width=border_thickness)
            else:
                state["_items"]["border"] = _create_rounded_rect(canvas, border_thickness/2, border_thickness/2, width-border_thickness/2, height-border_thickness/2, radius=radius, outline=border_color, width=border_thickness, fill="")

        # Lock Icon
        state["_items"]["lock"] = canvas.create_text(width-1, 1, text="🔒", fill="white", font=("Arial", 10), anchor="ne", state="hidden")
        
        # External Label
        if label_text and (not config.get("text_inside")):
            l_pos = config.get("label_position", "top").lower()
            lx, ly, l_anchor = width/2, 4, "n"
            if l_pos == "bottom": ly, l_anchor = height-4, "s"
            elif l_pos == "left": lx, ly, l_anchor = 2, height/2, "w"
            elif l_pos == "right": lx, ly, l_anchor = width-2, height/2, "e"
            l_font = config.get("font_size", 10) or 10
            state["_items"]["label"] = canvas.create_text(lx, ly, text=label_text, fill="white", font=("Helvetica", l_font, "bold"), anchor=l_anchor)

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
    bx, by = width/2, height/2
    is_horiz = width > height
    gap = (height if is_horiz else width) * state["current_open"]
    
    eff_shutter_col = shutter_color
    if state["is_hovering"] and shutter_color.lower() in ["black", "#000000"] and state["current_open"] < 0.5:
        eff_shutter_col = "#333333"

    if is_horiz:
        canvas.coords(state["_items"]["s1"], 0, 0, width, by - (gap/2))
        canvas.coords(state["_items"]["s2"], 0, by + (gap/2), width, height)
    else:
        canvas.coords(state["_items"]["s1"], 0, 0, bx - (gap/2), height)
        canvas.coords(state["_items"]["s2"], bx + (gap/2), 0, width, height)
    
    canvas.itemconfig(state["_items"]["s1"], fill=eff_shutter_col)
    canvas.itemconfig(state["_items"]["s2"], fill=eff_shutter_col)
    
    # Update Lock
    canvas.itemconfig(state["_items"]["lock"], state="normal" if state["is_locked"] else "hidden")
    
    # Ensure items are correctly stacked
    # Mask must be above shutters but below lens
    if "mask" in state["_items"]: canvas.tag_raise(state["_items"]["mask"], state["_items"]["s2"])
    if "lens" in state["_items"]: canvas.tag_raise(state["_items"]["lens"])
    if "border" in state["_items"]: canvas.tag_raise(state["_items"]["border"])
    if "label" in state["_items"]: canvas.tag_raise(state["_items"]["label"])
