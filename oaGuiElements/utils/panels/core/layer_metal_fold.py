from PIL import Image, ImageDraw
import math

class MetalFoldLayer:
    @staticmethod
    def generate_metal_fold(width, height, config):
        """
        Generates 3D panel folds (creases) and edge shadows.
        Now supports 'Segmented Panel' logic: each horizontal fold creates a new visual panel.
        """
        layer = Image.new('RGBA', (width, height), (0,0,0,0))
        draw = ImageDraw.Draw(layer)
        thickness = int(config.get("width_px", 20))
        
        creases = config.get("creases", [])
        
        # 1. Separate and sort creases to define segments
        h_creases = sorted([float(c.get("position_pct", 0.5)) for c in creases if c.get("orientation", "horizontal") == "horizontal"])
        # Add boundaries
        h_bounds = [0.0] + h_creases + [1.0]
        
        # 2. Draw Panel Effects for each segment
        for i in range(len(h_bounds) - 1):
            y_start = int(height * h_bounds[i])
            y_end = int(height * h_bounds[i+1])
            h_segment = y_end - y_start
            
            if h_segment <= 0: continue
            
            # --- Draw Segment Edges (Highlights and Shadows) ---
            # This is what makes it look like a 'New Panel'
            for j in range(thickness - 1, -1, -1):
                # Quadratic falloff for smooth transitions
                shadow_alpha = int(160 * math.pow(1.0 - j/thickness, 2))
                highlight_alpha = int(60 * math.pow(1.0 - j/thickness, 2))
                
                # Bottom Shadow of THIS segment (Ambient Occlusion)
                draw.line((0, y_end - 1 - j, width - 1, y_end - 1 - j), fill=(0, 0, 0, shadow_alpha))
                
                # Top Highlight of THIS segment (Simulated Overhead Light hitting the edge)
                draw.line((0, y_start + j, width - 1, y_start + j), fill=(255, 255, 255, highlight_alpha))
                
                # Left Highlight (Shared across full height, but we can segment it)
                draw.line((j, y_start, j, y_end), fill=(255, 255, 255, highlight_alpha))
                
                # Right Shadow (Shared across full height)
                draw.line((width - 1 - j, y_start, width - 1 - j, y_end), fill=(0, 0, 0, shadow_alpha))

            # --- Internal Crease Joint (The 'Gap') ---
            if i < len(h_bounds) - 2: # Don't draw at the very bottom of the whole image
                y = y_end
                # Draw a deeper physical gap
                # 1. Dark background for the gap
                draw.line((0, y, width - 1, y), fill=(0, 0, 0, 255), width=2)
                # 2. Subtle rim highlight on the top of the NEXT panel
                draw.line((0, y + 1, width - 1, y + 1), fill=(255, 255, 255, 40), width=1)
                
        # 3. Vertical Creases (Columns - keeping original logic for columns)
        v_creases = [c for c in creases if c.get("orientation") == "vertical"]
        for crease in v_creases:
            pos_pct = float(crease.get("position_pct", 0.5))
            if pos_pct < 0 or pos_pct > 1.0: continue
            x = int(width * pos_pct)
            # Highlight (left)
            draw.line((x-1, 0, x-1, height - 1), fill=(255, 255, 255, 60), width=1)
            # Shadow (right)
            draw.line((x+1, 0, x+1, height - 1), fill=(0, 0, 0, 100), width=2)
                
        return layer
                
        return layer
