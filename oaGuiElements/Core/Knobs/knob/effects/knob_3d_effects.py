# effects/knob_3d_effects.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from PIL import Image, ImageDraw, ImageFilter, ImageTk


def draw_knob_3d_effects(canvas, cx, cy, radius, shape, fill_color):
    """
    Renders 3D lighting effects (top-left glint, bottom-right shadow) 
    for the knob body. These effects remain fixed and do not rotate.
    """
    width = int(radius * 2.5)
    height = int(radius * 2.5)

    # Check if we need to regenerate
    cache_key = (radius, shape, fill_color)
    if (not hasattr(canvas, 'knob_3d_image') or
        getattr(canvas, 'last_knob_3d_key', None) != cache_key):

        canvas.last_knob_3d_key = cache_key

        # Create a base image with transparency
        # We make it slightly larger than the radius to account for blur
        img_size = int(radius * 2.2)
        if img_size < 1: img_size = 1

        fx_img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(fx_img)

        # Local center in the fx_img
        lcx, lcy = img_size / 2, img_size / 2
        r = radius

        # 1. Shadow (Bottom-Right)
        shadow_layer = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(shadow_layer)
        # Shift shadow slightly down-right
        sh_offset = r * 0.1
        if shape == "circle":
            sh_draw.ellipse((lcx - r + sh_offset, lcy - r + sh_offset, lcx + r + sh_offset, lcy + r + sh_offset), fill=(0, 0, 0, 80))
        elif shape in ["octagon", "gear"]:
            # For simplicity in PIL, we'll use a blurred circle shadow even for gears to give a soft drop-shadow look
            sh_draw.ellipse((lcx - r + sh_offset, lcy - r + sh_offset, lcx + r + sh_offset, lcy + r + sh_offset), fill=(0, 0, 0, 80))

        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=r*0.15))
        fx_img = Image.alpha_composite(fx_img, shadow_layer)

        # 2. Glint (Top-Left)
        glint_layer = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glint_layer)
        # Glint oval skewed top-left
        g_r_w = r * 0.6
        g_r_h = r * 0.3
        g_ox = lcx - r * 0.4
        g_oy = lcy - r * 0.5

        g_draw.ellipse((g_ox - g_r_w, g_oy - g_r_h, g_ox + g_r_w, g_oy + g_r_h), fill=(255, 255, 255, 100))

        glint_layer = glint_layer.filter(ImageFilter.GaussianBlur(radius=r*0.2))
        fx_img = Image.alpha_composite(fx_img, glint_layer)

        # 3. Inner Rim Highlight (Fixed Top-Left)
        rim_layer = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        r_draw = ImageDraw.Draw(rim_layer)
        r_draw.arc((lcx - r, lcy - r, lcx + r, lcy + r), start=180, end=270, fill=(255, 255, 255, 60), width=2)
        rim_layer = rim_layer.filter(ImageFilter.GaussianBlur(radius=1))
        fx_img = Image.alpha_composite(fx_img, rim_layer)

        canvas.knob_3d_image = ImageTk.PhotoImage(fx_img)

    # Draw the effect image centered at cx, cy
    # Note: create_image anchor is usually NW by default, but we want center
    img_id = canvas.create_image(cx, cy, image=canvas.knob_3d_image, anchor="center")
    return img_id
