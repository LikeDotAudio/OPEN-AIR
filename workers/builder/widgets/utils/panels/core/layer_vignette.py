from PIL import Image, ImageDraw, ImageFilter
import math

class VignetteLayer:
    @staticmethod
    def generate_linear_gradient(width, height, intensity):
        """Creates a soft vertical gradient simulating overhead lighting (Top to Bottom)."""
        base = Image.new('L', (width, height), 255)
        draw = ImageDraw.Draw(base)
        for y in range(height):
            # Overhead light: Top is brightest (255), Bottom is darkest (255 - intensity)
            # We fade the alpha factor linearly.
            alpha_factor = 1.0 - (y / height) * (intensity * 0.15)
            draw.line((0, y, width - 1, y), fill=int(255 * alpha_factor))
        return base.convert("RGBA")

    @staticmethod
    def generate_vignette(width, height, intensity, depth=110):
        """Creates a robust 4-sided vignette fading from all edges."""
        if depth <= 0:
            return Image.new('RGBA', (width, height), (255, 255, 255, 255))
            
        # Start with white (no effect when multiplied)
        vig = Image.new('L', (width, height), 255)
        draw = ImageDraw.Draw(vig)
        
        # Ensure intensity is clamped
        intensity = max(0.0, min(1.0, intensity))
        
        # Draw a gradient that fades inwards from all 4 sides.
        for i in range(depth):
            progress = i / depth
            # Nonlinear falloff for a "lens" look
            alpha_factor = 1.0 - (math.pow(1.0 - progress, 1.2) * intensity * 0.8)
            alpha = int(255 * alpha_factor)
            
            # Draw rectangles to ensure 4-sided coverage without gaps
            draw.rectangle((i, i, width-1-i, height-1-i), outline=alpha)
            
        # Apply a heavy blur to soften the transitions further
        blur_radius = max(2, depth // 2)
        return vig.filter(ImageFilter.GaussianBlur(radius=blur_radius)).convert("RGBA")
