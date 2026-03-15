import math
from workers.styling.style import THEMES, DEFAULT_THEME

class TrapezoidRendererMixin:
    """Handles the rendering logic and mathematics for the 3D Trapezoidal button."""

    def _draw_trapezoid_button(self, canvas, config, state):
        """Draws the complete trapezoid button assembly."""
        canvas.delete("button_elements")
        
        # Preserve industrial background
        for item in canvas.find_all():
            tags = canvas.gettags(item)
            if "panel_bg_slice" not in tags and "industrial_text" not in tags:
                canvas.delete(item)

        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
            canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

        w = int(canvas.winfo_width()) if canvas.winfo_width() > 1 else config.get("width", 80)
        h = int(canvas.winfo_height()) if canvas.winfo_height() > 1 else config.get("height", 50) + (25 if state.get("label") else 0)

        cw, ch = w / 2, h / 2
        bw, bh = w * 0.8, config.get("height", 50) * 0.8

        pressed, lit = state.get("pressed", False), state.get("lit", False)
        base_color, led_color = state.get("base_color", "#8B0000"), state.get("led_color", "#FF0000")
        btn_text, lbl = config.get("button_text", ""), state.get("label")

        # Offset for pressed state
        dy = 4 if pressed else 0

        # Colors
        shadow_color = "#111111"
        face_color = self._adjust_color_lightness(base_color, 0.8 if pressed else 1.0)
        top_bevel = self._adjust_color_lightness(base_color, 1.2 if not pressed else 0.9)
        bottom_bevel = self._adjust_color_lightness(base_color, 0.5)
        side_bevel = self._adjust_color_lightness(base_color, 0.7)
        ind_color = led_color if lit else "#330000"

        # Geometry
        bx, by = cw - bw / 2, ch - bh / 2 - (10 if lbl else 0)
        if lbl: by += 10
        
        y_offset = by + dy
        bevel_w, top_shrink = bw * 0.15, bw * 0.1

        p_outer = [bx, y_offset + bh, bx + top_shrink, y_offset, bx + bw - top_shrink, y_offset, bx + bw, y_offset + bh]
        p_inner = [bx + bevel_w, y_offset + bh - bevel_w, bx + top_shrink + bevel_w * 0.5, y_offset + bevel_w,
                   bx + bw - top_shrink - bevel_w * 0.5, y_offset + bevel_w, bx + bw - bevel_w, y_offset + bh - bevel_w]

        # Draw Layers
        if not pressed:
            canvas.create_polygon([bx - 2, by + bh + 6, bx + top_shrink - 2, by + 6, bx + bw - top_shrink + 2, by + 6, bx + bw + 2, by + bh + 6], fill=shadow_color, outline="", tags="button_elements")

        canvas.create_polygon(p_outer, fill=face_color, outline="#222222", width=1, tags="button_elements")
        
        # Bevels
        canvas.create_polygon([p_outer[0], p_outer[1], p_inner[0], p_inner[1], p_inner[6], p_inner[7], p_outer[6], p_outer[7]], fill=bottom_bevel, outline="", tags="button_elements")
        canvas.create_polygon([p_outer[2], p_outer[3], p_inner[2], p_inner[3], p_inner[4], p_inner[5], p_outer[4], p_outer[5]], fill=top_bevel, outline="", tags="button_elements")
        canvas.create_polygon([p_outer[0], p_outer[1], p_inner[0], p_inner[1], p_inner[2], p_inner[3], p_outer[2], p_outer[3]], fill=side_bevel, outline="", tags="button_elements")
        canvas.create_polygon([p_outer[6], p_outer[7], p_inner[6], p_inner[7], p_inner[4], p_inner[5], p_outer[4], p_outer[5]], fill=side_bevel, outline="", tags="button_elements")
        
        canvas.create_polygon(p_inner, fill=face_color, outline="", tags="button_elements")

        # Indicator
        iw, ih = bw * 0.4, bh * 0.15
        ix, iy = cw - iw / 2, y_offset + bh * 0.2
        canvas.create_rectangle(ix, iy, ix + iw, iy + ih, fill=ind_color, outline="#111111", width=1, tags="button_elements")

        if lit:
            glow_w = iw * 1.5
            glow_h = ih * 2
            glow_x = cw - glow_w / 2
            glow_y = iy + ih / 2 - glow_h / 2
            canvas.create_oval(glow_x, glow_y, glow_x + glow_w, glow_y + glow_h, fill="", outline=ind_color, width=2, stipple="gray50", tags="button_elements")

        if btn_text:
            canvas.create_text(cw, y_offset + bh * 0.6, text=btn_text, fill="white", font=("Arial", 9, "bold"), tags="button_elements")

        if lbl:
            txt_col = THEMES.get(DEFAULT_THEME, THEMES["dark"]).get("fg", "#dcdcdc")
            canvas.delete("industrial_text")
            canvas.create_text(cw, by - 10, text=lbl, fill=txt_col, font=("Arial", 8, "bold"), anchor="s", tags="industrial_text")

    def _adjust_color_lightness(self, hex_color, factor):
        """Helper to lighten/darken a hex color."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3: hex_color = ''.join([c*2 for c in hex_color])
        try:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except: return "#8B0000"
