from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import random
import math

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.Display.factory.asset_cache import AssetCacheManager

# Sizing and Geometry Constants
CANVAS_PADDING_RATIO = 0.4
CENTER_DIVISOR = 2
RADIUS_DIVISOR = 2
OFFSET_RATIO_FILLISTER = 0.15
SHADOW_BLUR_RATIO_FILLISTER = 0.1
SHADOW_BLUR_RATIO_COUNTERSUNK = 0.05
SPECULAR_OFFSET_RATIO = 0.3
DRIVE_SIZE_RATIO = 0.55
ROTATION_RANGE_MAX = 90

# Color and Alpha Constants
DEFAULT_SHADOW_ALPHA = 150
MAX_ALPHA_VALUE = 255
AMBIENT_LIGHT_LEVEL = 100
HIGHLIGHT_LIGHT_LEVEL = 255
COUNTERSUNK_LIGHT_LEVEL = 180
LIGHTING_STRENGTH_RATIO = 0.5
VOID_COLOR_RGBA = (20, 20, 20, 240)
NORTH_WALL_ILLUMINATION = (100, 100, 100, 200)
WEST_WALL_ILLUMINATION = (80, 80, 80, 200)
EAST_WALL_SHADOW = (10, 10, 10, 255)
SOUTH_WALL_DEEP_SHADOW = (0, 0, 0, 255)
SCRATCH_SILVER_EXPOSURE = (200, 200, 200, 150)
RUST_BASE_COLOR_RGB = (130, 60, 20)

# Damage and Wear Constants
SCRATCH_COUNT_BASE = 5
START_DISTANCE_RATIO = 0.6
END_DISTANCE_RATIO = 0.9
S_ANGLE_MAX = 360
RUST_NOISE_SIGMA = 50
RUST_RESIZE_RATIO = 1.5
RUST_OFFSET_RATIO = 0.75

class ScrewGenerator:
    """
    Procedural generator for high-fidelity Robertson screws.
    Supports Fillister (Domed) and Countersunk heads with physical lighting and wear models.
    """

    @staticmethod
    def generate_procedural_screw(size_pixels, configuration_data={}):
        """
        Generates a single screw image (RGBA) centered in a square canvas.
        Includes disk caching to prevent redundant generation.
        """
        # --- 0. Check Cache First ---
        if BUILDER_DEBUG: builder_logger.trace(f"📦🔍✨ [CACHE] Checking for procedural screw in cache: {size_pixels}px")
        cached_image = AssetCacheManager.load_from_cache("screw", size_pixels, size_pixels, configuration_data)
        if cached_image:
            if BUILDER_DEBUG: builder_logger.debug(f"📦🆗✅ [CACHE] Retaining procedural screw from disk cache.")
            return cached_image

        # --- 1. Procedural Generation ---
        if BUILDER_DEBUG: builder_logger.info(f"🔩🏗️🌀 [BUILDER] Generating NEW Procedural Screw ({size_pixels}px)")
        # Canvas setup (padding for drop shadow)
        padding_amount = int(size_pixels * CANVAS_PADDING_RATIO)
        canvas_dimension = size_pixels + (padding_amount * 2)
        center_coordinate = canvas_dimension // CENTER_DIVISOR
        screw_radius = size_pixels // RADIUS_DIVISOR
        
        screw_image = Image.new('RGBA', (canvas_dimension, canvas_dimension), (0,0,0,0))
        # draw_context = ImageDraw.Draw(screw_image)
        
        screw_head_type = configuration_data.get("type", "fillister")
        material_finish = configuration_data.get("finish", "chrome")
        base_color_hex = configuration_data.get("color", "#cccccc") if material_finish == "custom" else \
                         "#e0e0e0" if material_finish == "chrome" else "#222222"
        
        damage_intensity = float(configuration_data.get("damage", 0.0))
        rust_intensity = float(configuration_data.get("rust", 0.0))
        rotation_angle_degrees = float(configuration_data.get("angle", random.randint(0, ROTATION_RANGE_MAX)))
        if BUILDER_DEBUG: builder_logger.debug(f"⚙️🔘✅ [CONFIG] Type: {screw_head_type}, Finish: {material_finish}, Rotation: {rotation_angle_degrees:.1f}°")

        # --- 1. Drop Shadow (The External Cast) ---
        if BUILDER_DEBUG: builder_logger.trace("👻🌀🔳 [LAYER] 1. Casting external drop shadow.")
        shadow_layer_image = Image.new('RGBA', (canvas_dimension, canvas_dimension), (0,0,0,0))
        shadow_draw_context = ImageDraw.Draw(shadow_layer_image)
        
        if screw_head_type == "fillister":
            # Long, directional shadow for tall head
            # Offset to bottom-right (simulating top-left light)
            offset_x = int(size_pixels * OFFSET_RATIO_FILLISTER)
            offset_y = int(size_pixels * OFFSET_RATIO_FILLISTER)
            shadow_draw_context.ellipse((center_coordinate - screw_radius + offset_x, center_coordinate - screw_radius + offset_y,
                            center_coordinate + screw_radius + offset_x, center_coordinate + screw_radius + offset_y),
                           fill=(0, 0, 0, DEFAULT_SHADOW_ALPHA))
            shadow_blur_radius = size_pixels * SHADOW_BLUR_RATIO_FILLISTER
        else:
            # Countersunk has almost no drop shadow, just a recess shade
            shadow_blur_radius = size_pixels * SHADOW_BLUR_RATIO_COUNTERSUNK
            
        shadow_layer_image = shadow_layer_image.filter(ImageFilter.GaussianBlur(shadow_blur_radius))
        screw_image = Image.alpha_composite(shadow_layer_image, screw_image)

        # --- 2. The Head Geometry ---
        if BUILDER_DEBUG: builder_logger.trace(f"🎨🖌️🔘 [LAYER] 2. Lathe-turning screw head: {base_color_hex}")
        head_layer_image = Image.new('RGBA', (canvas_dimension, canvas_dimension), (0,0,0,0))
        head_draw_context = ImageDraw.Draw(head_layer_image)
        
        base_color_rgb = ScrewGenerator.convert_hex_to_rgb(base_color_hex)
        
        # Base Circle
        head_draw_context.ellipse((center_coordinate - screw_radius, center_coordinate - screw_radius, center_coordinate + screw_radius, center_coordinate + screw_radius), 
                       fill=base_color_rgb + (MAX_ALPHA_VALUE,))
        
        # Lighting Model (Sphere/Dome or Cone)
        lighting_mask_image = Image.new('L', (canvas_dimension, canvas_dimension), 0)
        lighting_draw_context = ImageDraw.Draw(lighting_mask_image)
        
        if screw_head_type == "fillister":
            # Domed top: Radial gradient highlight shifted top-left
            # Specular highlight
            specular_offset = int(screw_radius * SPECULAR_OFFSET_RATIO)
            lighting_draw_context.ellipse((center_coordinate - screw_radius, center_coordinate - screw_radius, center_coordinate + screw_radius, center_coordinate + screw_radius), fill=AMBIENT_LIGHT_LEVEL) # Ambient
            lighting_draw_context.ellipse((center_coordinate - screw_radius + specular_offset, center_coordinate - screw_radius + specular_offset, 
                            center_coordinate, center_coordinate), fill=HIGHLIGHT_LIGHT_LEVEL) # Highlight
            lighting_mask_image = lighting_mask_image.filter(ImageFilter.GaussianBlur(screw_radius * 0.5))
        else:
            # Countersunk: Conical gradient (Rim is bright, center is deeper)
            lighting_draw_context.ellipse((center_coordinate - screw_radius, center_coordinate - screw_radius, center_coordinate + screw_radius, center_coordinate + screw_radius), fill=COUNTERSUNK_LIGHT_LEVEL)
        
        # Apply Lighting to Color using Multiply/Overlay
        lighting_rgba_image = ImageOps.colorize(lighting_mask_image, black="black", white="white").convert("RGBA")
        lighting_rgba_image.putalpha(Image.eval(lighting_mask_image, lambda alpha: int(alpha * LIGHTING_STRENGTH_RATIO))) # Adjust strength
        
        # Composite Head + Light
        head_layer_image = Image.alpha_composite(head_layer_image, lighting_rgba_image)
        
        # Mask to circle
        clipping_mask_image = Image.new('L', (canvas_dimension, canvas_dimension), 0)
        clipping_draw_context = ImageDraw.Draw(clipping_mask_image)
        clipping_draw_context.ellipse((center_coordinate - screw_radius, center_coordinate - screw_radius, center_coordinate + screw_radius, center_coordinate + screw_radius), fill=MAX_ALPHA_VALUE)
        head_layer_image.putalpha(ImageChops.multiply(head_layer_image.split()[3], clipping_mask_image))
        
        screw_image = Image.alpha_composite(screw_image, head_layer_image)

        # --- 3. The Robertson Void (Square Drive) ---
        if BUILDER_DEBUG: builder_logger.trace("🔳📐🕳️ [LAYER] 3. Punching Robertson square drive void.")
        drive_size_pixels = screw_radius * DRIVE_SIZE_RATIO
        
        drive_layer_image = Image.new('RGBA', (canvas_dimension, canvas_dimension), (0,0,0,0))
        drive_draw_context = ImageDraw.Draw(drive_layer_image)
        
        # Coordinates of square vertices
        rotation_angle_radians = math.radians(rotation_angle_degrees)
        half_drive_size = drive_size_pixels / 2
        
        # Points unrotated relative to center
        square_points = [(-half_drive_size, -half_drive_size), (half_drive_size, -half_drive_size), (half_drive_size, half_drive_size), (-half_drive_size, half_drive_size)]
        rotated_square_points = []
        for local_x, local_y in square_points:
            rotated_x = local_x * math.cos(rotation_angle_radians) - local_y * math.sin(rotation_angle_radians) + center_coordinate
            rotated_y = local_x * math.sin(rotation_angle_radians) + local_y * math.cos(rotation_angle_radians) + center_coordinate
            rotated_square_points.append((rotated_x, rotated_y))
            
        # Draw the Void (Dark Hole)
        drive_draw_context.polygon(rotated_square_points, fill=VOID_COLOR_RGBA)
        
        # Internal Shadows simulation
        point0, point1, point2, point3 = rotated_square_points
        
        # "North" Wall: Illuminated
        drive_draw_context.line((point0, point1), fill=NORTH_WALL_ILLUMINATION, width=2)
        # "West" Wall: Illuminated
        drive_draw_context.line((point3, point0), fill=WEST_WALL_ILLUMINATION, width=2)
        # "East" Wall: Shadow
        drive_draw_context.line((point1, point2), fill=EAST_WALL_SHADOW, width=2)
        # "South" Wall: Deep Shadow
        drive_draw_context.line((point2, point3), fill=SOUTH_WALL_DEEP_SHADOW, width=2)
        
        screw_image = Image.alpha_composite(screw_image, drive_layer_image)

        # --- 4. Damage & Wear (Cam-out & Scratches) ---
        if damage_intensity > 0:
            if BUILDER_DEBUG: builder_logger.trace(f"🗡️🎨✨ [LAYER] 4. Applying screwdriver slippage wear (Int: {damage_intensity})")
            scratch_layer_image = Image.new('RGBA', (canvas_dimension, canvas_dimension), (0,0,0,0))
            scratch_draw_context = ImageDraw.Draw(scratch_layer_image)
            
            # Scratches radiating from the drive (Slippage)
            num_slippage_scratches = int(SCRATCH_COUNT_BASE * damage_intensity) + 1
            for _ in range(num_slippage_scratches):
                scratch_angle_degrees = random.uniform(0, S_ANGLE_MAX)
                start_distance = drive_size_pixels * START_DISTANCE_RATIO
                end_distance = screw_radius * END_DISTANCE_RATIO
                
                start_x = center_coordinate + math.cos(math.radians(scratch_angle_degrees)) * start_distance
                start_y = center_coordinate + math.sin(math.radians(scratch_angle_degrees)) * start_distance
                end_x = center_coordinate + math.cos(math.radians(scratch_angle_degrees)) * end_distance
                end_y = center_coordinate + math.sin(math.radians(scratch_angle_degrees)) * end_distance
                
                # Metal groove highlight
                scratch_draw_context.line((start_x, start_y, end_x, end_y), fill=SCRATCH_SILVER_EXPOSURE, width=1)
                
            screw_image = Image.alpha_composite(screw_image, scratch_layer_image)

        # --- 5. Rust (Accumulation) ---
        if rust_intensity > 0:
            if BUILDER_DEBUG: builder_logger.trace(f"🟠🎨✨ [LAYER] 5. Accumulating iron oxide rust (Int: {rust_intensity})")
            
            # Noise texture for rust
            noise_dimension = int(drive_size_pixels)
            rust_noise_texture = Image.effect_noise((noise_dimension, noise_dimension), sigma=RUST_NOISE_SIGMA).resize((int(drive_size_pixels * RUST_RESIZE_RATIO), int(drive_size_pixels * RUST_RESIZE_RATIO)))
            rust_noise_texture = rust_noise_texture.convert("RGBA")
            
            # Colorize rust noise (Orange/Brown)
            rust_alpha_level = int(MAX_ALPHA_VALUE * rust_intensity)
            rust_color_layer = Image.new("RGBA", rust_noise_texture.size, RUST_BASE_COLOR_RGB + (rust_alpha_level,))
            rust_composite_texture = ImageChops.multiply(rust_noise_texture, rust_color_layer)
            
            # Paste over drive center
            rust_offset_coordinate = int(center_coordinate - drive_size_pixels * RUST_OFFSET_RATIO)
            screw_image.paste(rust_composite_texture, (rust_offset_coordinate, rust_offset_coordinate), rust_composite_texture)

        # --- 6. Save to Cache ---
        if BUILDER_DEBUG: builder_logger.success(f"🎨🆗💾 [SUCCESS] Procedural screw generation complete. Saving to cache.")
        AssetCacheManager.save_to_cache("screw", size_pixels, size_pixels, configuration_data, screw_image)

        return screw_image

    @staticmethod
    def convert_hex_to_rgb(hex_string):
        """Converts a hexadecimal color string to an RGB tuple."""
        if not isinstance(hex_string, str): 
            return (128, 128, 128)
        color_hex = hex_string.lstrip('#')
        return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
