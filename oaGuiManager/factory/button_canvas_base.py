# managers/Display/core/button_canvas_base.py
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFont, ImageFilter, ImageChops
from loguru import logger

# --- Constants ---
DEFAULT_CORNER_RADIUS = 6
DEFAULT_PADDING = 4
MIN_SIZE_FOR_TEXTURE = 12
GLOW_SAMPLES = 15
DEFAULT_GLOW_RED = 255
DEFAULT_GLOW_GREEN = 150
DEFAULT_GLOW_BLUE = 0
DEFAULT_FONT_SIZE = 12
MAX_ALPHA = 255

class CanvasButton(tk.Canvas):
    """
    A custom Canvas-based button that supports photorealistic 'Backlit Glass Bar' rendering.
    Uses PIL to generate multi-layer textures (Well, Diffuser, Emitter, Legend, Lens).
    """
    def __init__(self, parent, text, command, 
                 width=100, height=50, 
                 corner_radius=DEFAULT_CORNER_RADIUS, 
                 pillow_mode=False,
                 bg_color=None, 
                 active_color="#FF9900", 
                 active_bg_color="#000000", 
                 text_color="#888888", 
                 active_text_color="#1a1a1a", 
                 glow_intensity=1.0,
                 active_font_style="bold",
                 active_font_size=None,
                 inactive_font_style="bold",
                 inactive_font_size=None,
                 alpha=1.0,
                 font=("TkDefaultFont", 10),
                 transparency_applicator=None,
                 config=None,
                 builder=None):
        
        # ⚡ Default bg_color to parent theme if None
        if bg_color is None:
            bg_color = "#2b2b2b"

        super().__init__(parent, width=width, height=height, bd=0, highlightthickness=0)
        
        self.text = text
        self.command = command
        self.corner_radius = corner_radius
        self.pillow_mode = pillow_mode
        self.bg_color = bg_color
        self.active_color = active_color
        self.active_bg_color = active_bg_color
        self.text_color = text_color
        self.active_text_color = active_text_color
        self.glow_intensity = float(glow_intensity)
        self.active_font_style = active_font_style
        self.active_font_size = active_font_size
        self.inactive_font_style = inactive_font_style
        self.inactive_font_size = inactive_font_size
        self.alpha = alpha
        self.font_info = font 
        
        self.is_circular = False
        if config:
            style = config.get("style", {})
            if isinstance(style, dict):
                self.is_circular = style.get("Circular", False)

        self.is_active = False
        self.is_locked = False # ⚡ INTERACTION LOCK
        self.is_hovered = False
        self._img_cache = {}
        self.last_size = (0, 0)
        
        if transparency_applicator and config and builder:
            transparency_applicator(self, self, config, builder)
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._on_resize)
        self._draw()

    def set_active(self, active):
        if self.is_active != active:
            self.is_active = active
            self._draw()

    def set_text(self, text):
        if self.text != text:
            self.text = text
            self._img_cache = {}
            self._draw()

    def _on_click(self, event):
        if self.command:
            self.is_locked = True # ⚡ LOCK
            try:
                self.command(event)
            finally:
                # Use after(100) to ensure any following network messages are blocked for a brief moment
                self.after(100, lambda: setattr(self, 'is_locked', False))

    def _on_enter(self, event):
        self.is_hovered = True; self._draw()

    def _on_leave(self, event):
        self.is_hovered = False; self._draw()

    def _on_resize(self, event):
        if (event.width, event.height) != self.last_size:
            self.last_size = (event.width, event.height)
            self._img_cache = {}; self._draw()

    def _get_color(self, color_spec):
        """Returns a valid color or safe fallback for Pillow."""
        if not color_spec or color_spec == "":
            # Safe fallback to project standard background or transparent.
            return "#2b2b2b" 
        if color_spec == "transparent":
            return (0, 0, 0, 0)
        return color_spec

    def _generate_rect_glass_texture(self, width, height, is_active, is_hovered, text, base_color, glow_color):
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        padding = DEFAULT_PADDING
        if width < MIN_SIZE_FOR_TEXTURE or height < MIN_SIZE_FOR_TEXTURE: return ImageTk.PhotoImage(image)
        
        radius = min(self.corner_radius, (width - padding*2)//2, (height - padding*2)//2)
        
        # 0. Shadow
        shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ImageDraw.Draw(shadow_layer).rounded_rectangle((padding-1, padding-1, width-padding+1, height-padding+1), radius=radius+1, fill=(0, 0, 0, 150))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=2))
        image = Image.alpha_composite(image, shadow_layer)

        # 1. Well
        well_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        well_draw = ImageDraw.Draw(well_layer)
        well_draw.rounded_rectangle((padding, padding, width-padding, height-padding), radius=radius, fill="#0a0a0a", outline=(26, 26, 26, 180), width=1)
        if height > padding*2 + 6:
            well_draw.rounded_rectangle((padding+1, padding+1, width-padding-1, padding+5), radius=radius, fill="#000000")
        image = Image.alpha_composite(image, well_layer)

        # 2. Body
        inner_pad = padding + 1
        body_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        body_draw = ImageDraw.Draw(body_layer)
        body_draw.rounded_rectangle((inner_pad, inner_pad, width-inner_pad, height-inner_pad), radius=radius, fill=self._get_color(self.active_bg_color if is_active else self.bg_color))
        
        if is_active:
            glow_layer = Image.new("RGBA", (width, height), (0,0,0,0))
            glow_draw = ImageDraw.Draw(glow_layer)
            try: red, green, blue = Image.new("RGB", (1,1), glow_color).getpixel((0,0))
            except Exception as e:
                logger.trace(f"Error getting glow color {glow_color}: {e}")
                red, green, blue = DEFAULT_GLOW_RED, DEFAULT_GLOW_GREEN, DEFAULT_GLOW_BLUE
            
            for i in range(GLOW_SAMPLES):
                alpha = int(MAX_ALPHA * (0.1 + 0.9 * ((i/GLOW_SAMPLES)**2)) * self.glow_intensity)
                hot = (i/GLOW_SAMPLES)**3
                current_col = (int(red+(MAX_ALPHA-red)*hot), int(green+(MAX_ALPHA-green)*hot), int(blue+(MAX_ALPHA-blue)*hot), alpha)
                sx, sy = int(width*0.8*(1-i/GLOW_SAMPLES)), int(height*1.5*(1-i/GLOW_SAMPLES))
                glow_draw.ellipse((width//2-sx, height//2-sy, width//2+sx, height//2+sy), fill=current_col)
            body_layer = Image.alpha_composite(body_layer, glow_layer.filter(ImageFilter.GaussianBlur(radius=8)))

        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).rounded_rectangle((inner_pad, inner_pad, width-inner_pad, height-inner_pad), radius=radius, fill=MAX_ALPHA)
        temp_body = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        temp_body.paste(body_layer, (0, 0), mask)
        image = Image.alpha_composite(image, temp_body)

        # 3. Legend
        if text:
            draw = ImageDraw.Draw(image)
            font_size = self.active_font_size if is_active else self.inactive_font_size
            if not font_size: font_size = int(self.font_info[1]) if len(self.font_info)>1 else DEFAULT_FONT_SIZE
            try: font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
            except Exception as e:
                logger.trace(f"Error loading font: {e}")
                font = ImageFont.load_default()
            
            # ⚡ HIGH-PRECISION CENTERING: Use anchor="mm" and align="center"
            text_x, text_y = width / 2, height / 2
            if is_hovered: text_y += 1
            draw.text((text_x, text_y), text, font=font, fill=self.active_text_color if is_active else self.text_color, anchor="mm", align="center")

        return ImageTk.PhotoImage(image)

    def _generate_circular_glass_texture(self, width, height, is_active, is_hovered, text, base_color, glow_color):
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        padding = DEFAULT_PADDING
        if width < MIN_SIZE_FOR_TEXTURE or height < MIN_SIZE_FOR_TEXTURE: return ImageTk.PhotoImage(image)
        
        radius = (min(width, height) - padding*2) // 2
        center_x, center_y = width//2, height//2
        
        # 0. Shadow
        shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ImageDraw.Draw(shadow_layer).ellipse((center_x-radius-1, center_y-radius-1, center_x+radius+1, center_y+radius+1), fill=(0, 0, 0, 150))
        image = Image.alpha_composite(image, shadow_layer.filter(ImageFilter.GaussianBlur(radius=2)))

        # 1. Well
        well_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ImageDraw.Draw(well_layer).ellipse((center_x-radius, center_y-radius, center_x+radius, center_y+radius), fill="#0a0a0a", outline=(26, 26, 26, 180), width=1)
        image = Image.alpha_composite(image, well_layer)

        # 2. Body
        body_radius = radius - 1
        body_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        body_draw = ImageDraw.Draw(body_layer)
        body_draw.ellipse((center_x-body_radius, center_y-body_radius, center_x+body_radius, center_y+body_radius), fill=self.active_bg_color if is_active else self.bg_color)
        
        if is_active:
            glow_layer = Image.new("RGBA", (width, height), (0,0,0,0))
            glow_draw = ImageDraw.Draw(glow_layer)
            try: red, green, blue = Image.new("RGB", (1,1), glow_color).getpixel((0,0))
            except Exception as e:
                logger.trace(f"Error getting circular glow color {glow_color}: {e}")
                red, green, blue = DEFAULT_GLOW_RED, DEFAULT_GLOW_GREEN, DEFAULT_GLOW_BLUE
            for i in range(GLOW_SAMPLES):
                alpha = int(MAX_ALPHA * (0.2+0.8*((i/GLOW_SAMPLES)**2)) * self.glow_intensity)
                hot = (i/GLOW_SAMPLES)**4
                curr_radius = int(body_radius*1.2*(1-i/GLOW_SAMPLES))
                glow_draw.ellipse((center_x-curr_radius, center_y-curr_radius, center_x+curr_radius, center_y+curr_radius), fill=(int(red+(MAX_ALPHA-red)*hot), int(green+(MAX_ALPHA-green)*hot), int(blue+(MAX_ALPHA-blue)*hot), alpha))
            body_layer = Image.alpha_composite(body_layer, glow_layer.filter(ImageFilter.GaussianBlur(radius=6)))

        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).ellipse((center_x-body_radius, center_y-body_radius, center_x+body_radius, center_y+body_radius), fill=MAX_ALPHA)
        temp_body = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        temp_body.paste(body_layer, (0, 0), mask)
        image = Image.alpha_composite(image, temp_body)

        if text:
            draw = ImageDraw.Draw(image)
            try: font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", DEFAULT_FONT_SIZE)
            except Exception as e:
                logger.trace(f"Error loading circular font: {e}")
                font = ImageFont.load_default()
            # ⚡ HIGH-PRECISION CENTERING: Use anchor="mm" and align="center"
            text_x, text_y = width / 2, height / 2
            if is_hovered: text_y += 1
            draw.text((text_x, text_y), text, font=font, fill=self.active_text_color if is_active else self.text_color, anchor="mm", align="center")

        return ImageTk.PhotoImage(image)

    def _draw(self):
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in self.find_all():
            tags = self.gettags(item)
            if "panel_bg_slice" not in tags:
                self.delete(item)
                
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1: return
        
        # ⚡ DETERMINISTIC COLORING: 
        # When inactive, use a fixed dark grey instead of inheriting background patina.
        # This makes the buttons feel like physical objects on the panel.
        
        effective_bg = self.bg_color
        
        if not self.is_active:
            # Default dark grey for inactive state
            effective_bg = "#1a1a1a" if self.bg_color in [None, "#2b2b2b"] else self.bg_color
            
            # Slightly lighter shade when hovered
            if self.is_hovered:
                effective_bg = "#333333" if effective_bg == "#1a1a1a" else effective_bg

        # ⚡ Only draw manual background if NO patina slice is available
        if hasattr(self, 'panel_bg_image') and not self.find_withtag("panel_bg_slice"):
             self.create_image(0, 0, image=self.panel_bg_image, anchor="nw", tags="panel_bg_slice")
             
        cache_key = (w, h, self.is_active, self.is_hovered, self.text, self.active_color, self.is_circular, effective_bg)
        if cache_key not in self._img_cache:
             self._img_cache[cache_key] = self._generate_circular_glass_texture(w,h,self.is_active,self.is_hovered,self.text,effective_bg,self.active_color) if self.is_circular else self._generate_rect_glass_texture(w,h,self.is_active,self.is_hovered,self.text,effective_bg,self.active_color)
        
        self.create_image(0, 0, image=self._img_cache[cache_key], anchor="nw")
