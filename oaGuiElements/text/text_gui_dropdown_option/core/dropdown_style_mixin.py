from tkinter import ttk

class DropdownStyleMixin:
    """Provides methods for blending colors and configuring TTK Combobox styles dynamically."""

    @staticmethod
    def _blend_colors(color1, color2, alpha=0.5):
        def hex_to_rgb(hex_str): return tuple(int(hex_str.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        def rgb_to_hex(rgb): return '#%02x%02x%02x' % rgb

        if not color1: color1 = "#000000"
        if not color2: color2 = "#ffffff"

        try:
            r1, g1, b1 = hex_to_rgb(color1)
            r2, g2, b2 = hex_to_rgb(color2)
            return rgb_to_hex((int(r1*(1-alpha) + r2*alpha), int(g1*(1-alpha) + g2*alpha), int(b1*(1-alpha) + b2*alpha)))
        except: return color1

    @classmethod
    def apply_style(cls, style_name, bg_color):
        blended_bg = cls._blend_colors(bg_color, "#ffffff", 0.5)
        style = ttk.Style()
        
        style.configure(style_name, 
            fieldbackground=blended_bg, foreground="white", 
            background=bg_color, arrowcolor="white", 
            bordercolor=bg_color, lightcolor=bg_color, darkcolor=bg_color
        )
        
        style.map(style_name, 
            fieldbackground=[("readonly", blended_bg), ("disabled", bg_color)],
            foreground=[("readonly", "white"), ("disabled", "grey")],
            background=[("readonly", bg_color)],
            arrowcolor=[("readonly", "white")]
        )
