from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import random
import math

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.Display.factory.asset_cache import AssetCacheManager

class ScrewGenerator:
    """
    Procedural generator for high-fidelity Robertson screws.
    Supports Fillister (Domed) and Countersunk heads with physical lighting and wear models.
    """

    @staticmethod
    def generate_screw(size_px, config={}):
        """
        Generates a single screw image (RGBA) centered in a square canvas.
        Includes disk caching to prevent redundant generation.
        """
        # --- 0. Check Cache First ---
        if BUILDER_DEBUG: builder_logger.trace(f"📦🔍✨ [CACHE] Checking for procedural screw in cache: {size_px}px")
        cached_img = AssetCacheManager.load_from_cache("screw", size_px, size_px, config)
        if cached_img:
            if BUILDER_DEBUG: builder_logger.debug(f"📦🆗✅ [CACHE] Retaining procedural screw from disk cache.")
            return cached_img

        # --- 1. Procedural Generation ---
        if BUILDER_DEBUG: builder_logger.info(f"🔩🏗️🌀 [BUILDER] Generating NEW Procedural Screw ({size_px}px)")
        # Canvas setup (padding for drop shadow)
        padding = int(size_px * 0.4)
        canvas_size = size_px + (padding * 2)
        center = canvas_size // 2
        radius = size_px // 2
        
        img = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        screw_type = config.get("type", "fillister")
        finish = config.get("finish", "chrome")
        base_color = config.get("color", "#cccccc") if finish == "custom" else \
                     "#e0e0e0" if finish == "chrome" else "#222222"
        
        damage_int = float(config.get("damage", 0.0))
        rust_int = float(config.get("rust", 0.0))
        rotation = float(config.get("angle", random.randint(0, 90)))
        if BUILDER_DEBUG: builder_logger.debug(f"⚙️🔘✅ [CONFIG] Type: {screw_type}, Finish: {finish}, Rotation: {rotation:.1f}°")

        # --- 1. Drop Shadow (The External Cast) ---
        if BUILDER_DEBUG: builder_logger.trace("👻🌀🔳 [LAYER] 1. Casting external drop shadow.")
        shadow_layer = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
        s_draw = ImageDraw.Draw(shadow_layer)
        
        if screw_type == "fillister":
            # Long, directional shadow for tall head
            # Offset to bottom-right (simulating top-left light)
            off_x, off_y = int(size_px * 0.15), int(size_px * 0.15)
            s_draw.ellipse((center - radius + off_x, center - radius + off_y,
                            center + radius + off_x, center + radius + off_y),
                           fill=(0, 0, 0, 150))
            shadow_blur = size_px * 0.1
        else:
            # Countersunk has almost no drop shadow, just a recess shade
            shadow_blur = size_px * 0.05
            
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
        img = Image.alpha_composite(shadow_layer, img)

        # --- 2. The Head Geometry ---
        if BUILDER_DEBUG: builder_logger.trace(f"🎨🖌️🔘 [LAYER] 2. Lathe-turning screw head: {base_color}")
        head_layer = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
        h_draw = ImageDraw.Draw(head_layer)
        
        rgb_color = ScrewGenerator._hex_to_rgb(base_color)
        
        # Base Circle
        h_draw.ellipse((center - radius, center - radius, center + radius, center + radius), 
                       fill=rgb_color + (255,))
        
        # Lighting Model (Sphere/Dome or Cone)
        lighting = Image.new('L', (canvas_size, canvas_size), 0)
        l_draw = ImageDraw.Draw(lighting)
        
        if screw_type == "fillister":
            # Domed top: Radial gradient highlight shifted top-left
            # Specular highlight
            spec_off = int(radius * 0.3)
            l_draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=100) # Ambient
            l_draw.ellipse((center - radius + spec_off, center - radius + spec_off, 
                            center, center), fill=255) # Highlight
            lighting = lighting.filter(ImageFilter.GaussianBlur(radius * 0.5))
        else:
            # Countersunk: Conical gradient (Rim is bright, center is deeper)
            # Actually flat top usually, but let's simulate the recess
            l_draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=180)
        
        # Apply Lighting to Color using Multiply/Overlay
        # Simplified: Just composite a gradient overlay
        lighting_rgba = ImageOps.colorize(lighting, black="black", white="white").convert("RGBA")
        lighting_rgba.putalpha(Image.eval(lighting, lambda a: int(a * 0.5))) # Adjust strength
        
        # Composite Head + Light
        head_layer = Image.alpha_composite(head_layer, lighting_rgba)
        
        # Mask to circle
        mask = Image.new('L', (canvas_size, canvas_size), 0)
        m_draw = ImageDraw.Draw(mask)
        m_draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=255)
        head_layer.putalpha(ImageChops.multiply(head_layer.split()[3], mask))
        
        img = Image.alpha_composite(img, head_layer)

        # --- 3. The Robertson Void (Square Drive) ---
        # Size: approx 1/3 of head diameter
        if BUILDER_DEBUG: builder_logger.trace("🔳📐🕳️ [LAYER] 3. Punching Robertson square drive void.")
        drive_size = radius * 0.55
        
        drive_layer = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
        d_draw = ImageDraw.Draw(drive_layer)
        
        # Coordinates of square vertices
        # Apply rotation
        angle_rad = math.radians(rotation)
        half_d = drive_size / 2
        
        # Points unrotated relative to center
        points = [(-half_d, -half_d), (half_d, -half_d), (half_d, half_d), (-half_d, half_d)]
        rotated_points = []
        for x, y in points:
            rx = x * math.cos(angle_rad) - y * math.sin(angle_rad) + center
            ry = x * math.sin(angle_rad) + y * math.cos(angle_rad) + center
            rotated_points.append((rx, ry))
            
        # Draw the Void (Dark Hole)
        # Deep shadow at bottom
        d_draw.polygon(rotated_points, fill=(20, 20, 20, 240))
        
        # Internal Shadows (The "Tapered Frustum" Logic)
        # Top-Left wall gets light (if light is top-left) -> Brighter grey
        # Bottom-Right wall is in shadow -> Black
        # Simple simulation: Gradient stroke
        # We simulate this by drawing lines along the edges with different brightness
        
        # Unpack for clarity (Order: TL, TR, BR, BL after rotation? No, index order is fixed)
        # With 0 rotation: 0=TL, 1=TR, 2=BR, 3=BL
        p0, p1, p2, p3 = rotated_points
        
        # "North" Wall (p0 to p1): Illuminated
        d_draw.line((p0, p1), fill=(100, 100, 100, 200), width=2)
        # "West" Wall (p3 to p0): Illuminated
        d_draw.line((p3, p0), fill=(80, 80, 80, 200), width=2)
        # "East" Wall (p1 to p2): Shadow
        d_draw.line((p1, p2), fill=(10, 10, 10, 255), width=2)
        # "South" Wall (p2 to p3): Deep Shadow
        d_draw.line((p2, p3), fill=(0, 0, 0, 255), width=2)
        
        img = Image.alpha_composite(img, drive_layer)

        # --- 4. Damage & Wear (Cam-out & Scratches) ---
        if damage_int > 0:
            if BUILDER_DEBUG: builder_logger.trace(f"🗡️🎨✨ [LAYER] 4. Applying screwdriver slippage wear (Int: {damage_int})")
            scratch_layer = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
            scr_draw = ImageDraw.Draw(scratch_layer)
            
            # Scratches radiating from the drive (Slippage)
            num_scratches = int(5 * damage_int) + 1
            for _ in range(num_scratches):
                # Start near drive
                s_angle = random.uniform(0, 360)
                start_dist = drive_size * 0.6
                end_dist = radius * 0.9
                
                sx = center + math.cos(math.radians(s_angle)) * start_dist
                sy = center + math.sin(math.radians(s_angle)) * start_dist
                ex = center + math.cos(math.radians(s_angle)) * end_dist
                ey = center + math.sin(math.radians(s_angle)) * end_dist
                
                # Metal groove: Dark line + Light highlight
                scr_draw.line((sx, sy, ex, ey), fill=(200, 200, 200, 150), width=1) # Silver exposure
                
            img = Image.alpha_composite(img, scratch_layer)

        # --- 5. Rust (Accumulation) ---
        if rust_int > 0:
            if BUILDER_DEBUG: builder_logger.trace(f"🟠🎨✨ [LAYER] 5. Accumulating iron oxide rust (Int: {rust_int})")
            rust_layer = Image.new('RGBA', (canvas_size, canvas_size), (0,0,0,0))
            r_draw = ImageDraw.Draw(rust_layer)
            
            # Rust mostly inside the drive hole and edges
            # Noise texture masked to drive
            rust_noise = Image.effect_noise((int(drive_size), int(drive_size)), sigma=50).resize((int(drive_size*1.5), int(drive_size*1.5)))
            rust_noise = rust_noise.convert("RGBA")
            
            # Colorize rust noise (Orange/Brown)
            rust_color = Image.new("RGBA", rust_noise.size, (130, 60, 20, int(255 * rust_int)))
            rust_comp = ImageChops.multiply(rust_noise, rust_color)
            
            # Paste over drive center
            offset = int(center - drive_size * 0.75)
            img.paste(rust_comp, (offset, offset), rust_comp)

        # --- 6. Save to Cache ---
        if BUILDER_DEBUG: builder_logger.success(f"🎨🆗💾 [SUCCESS] Procedural screw generation complete. Saving to cache.")
        AssetCacheManager.save_to_cache("screw", size_px, size_px, config, img)

        return img

    @staticmethod
    def _hex_to_rgb(hex_str):
        if not isinstance(hex_str, str): return (128, 128, 128)
        c = hex_str.lstrip('#')
        return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
