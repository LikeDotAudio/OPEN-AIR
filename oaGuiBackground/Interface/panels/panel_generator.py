# panels/panel_generator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

# --- Imports for the new modular architecture ---
from oaGuiElements.Methods.utils import PanelUtils
from oaGuiManager.Core.factory.asset_cache import AssetCacheManager

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import builder_logger

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import is_debug_allowed

from .Core.layer_dust import DustLayer
from .Core.layer_metal_fold import MetalFoldLayer
from .Core.layer_rust import RustLayer
from .Core.layer_scratches import ScratchLayer
from .Core.layer_screws import ScrewLayer
from .Core.layer_stains import StainsLayer
from .Core.layer_vignette import VignetteLayer
from .Core.substrate_factory import SubstrateFactory

BUILDER_DEBUG = is_debug_allowed(system="UI", element="GUI_BUILDER")

# Random Seed Constants
MAX_RANDOM_SEED = 1000000

# Texture Generation Constants
DEFAULT_GRAIN_INTENSITY = 0.15
WRINKLE_SIGMA = 80
STREAK_SIGMA_CROSSHATCH = 10
STREAK_SIGMA_BRUSHED = 20
STREAK_SIGMA_DEFAULT = 5
ENAMEL_RESIZE_FACTOR = 4

# Paint Layer Constants
MAX_OPACITY_VALUE = 255
DEFAULT_PAINT_OPACITY = 0.0
DEFAULT_EDGE_SCRATCH_DEPTH = 30
DEFAULT_EDGE_SCRATCH_INTENSITY = 0.5
EDGE_SCRATCH_COUNT_MULTIPLIER = 50
EDGE_SCRATCH_OFFSET_RANGE = 20
DEFAULT_MIN_SCRATCH_LENGTH = 20
DEFAULT_MAX_SCRATCH_LENGTH = 150
DEFAULT_SCRATCH_WIDTH = 1
SCRATCH_GAUSSIAN_BLUR_RADIUS = 1

# Haze and Gradient Constants
STUDIO_HAZE_COLOR = (180, 140, 50)
DEFAULT_HAZE_INTENSITY = 0.15
DEFAULT_GRADIENT_INTENSITY = 0.2

# Vignette and Fade Constants
DEFAULT_VIGNETTE_INTENSITY = 0.5
DEFAULT_FADE_DEPTH = 110

# Final Processing Constants
DEFAULT_GLOBAL_BLUR = 0.0

class PanelGenerator:
    """
    Advanced Procedural Panel Generator (Modular Version).
    Orchestrates specialized layer modules to simulate physical materials.
    """

    @staticmethod
    def generate_procedural_panel(width, height, configuration_data={}):
        """
        Generates a PIL Image based on detailed physical parameters.
        Includes disk caching to prevent redundant generation.
        """
        #prefer the 'parameters' key if it exists, otherwise use the top-level dict
        settings = configuration_data.get("parameters", configuration_data)

        # ⚡ RESOLUTION CONTROL: Extract scale_factor (default 1.0)
        scale_factor = float(settings.get("scale_factor", 1.0))

        # --- 0. Check Cache First ---
        if BUILDER_DEBUG: builder_logger.trace(f"📦🔍✨ [CACHE] Checking for procedural panel in cache: {width}x{height} (Scale: {scale_factor})")
        cached_image = AssetCacheManager.load_from_cache("panel", width, height, configuration_data)
        if cached_image:
            if BUILDER_DEBUG: builder_logger.debug("📦🆗✅ [CACHE] Retaining procedural panel from disk cache.")
            return cached_image

        # --- 1. Extract Parameters ---
        random_seed = settings.get("random_seed")
        if not random_seed:
            random_seed = random.randint(1, MAX_RANDOM_SEED)
        random.seed(random_seed)

        if BUILDER_DEBUG: builder_logger.info(f"🎨🏗️🌀 [BUILDER] Generating NEW Procedural Panel ({width}x{height}) Scale: {scale_factor} Seed: {random_seed}")

        # --- 2. Layer Configs ---
        base_material_settings = settings.get("base_material", {})
        paint_layer_settings = settings.get("paint_layer", {})
        edge_wear_settings = settings.get("edge_wear", {"enabled": False})
        panel_scratch_settings = settings.get("panel_scratches", settings.get("scratches", {"count": 0}))
        grime_settings = settings.get("grime", {"stain_count": 0})
        rust_settings = settings.get("rust", {"enabled": False})
        dust_settings = settings.get("dust", {"enabled": False, "intensity": 0.3})
        screws_settings = settings.get("screws", {"enabled": False})
        fold_settings = settings.get("metal_fold", {"enabled": False})
        haze_settings = settings.get("studio_haze", {"enabled": False})

        # --- Layer 1: The Substrate (The Metal Panel) ---
        substrate_color_hex = base_material_settings.get("color", "#2a2a2a")
        if BUILDER_DEBUG: builder_logger.trace(f"🎨🖌️🔳 [LAYER] 1. Substrate: {substrate_color_hex}")
        substrate_color_rgba = PanelUtils.hex_to_rgba(substrate_color_hex)
        panel_image = Image.new('RGBA', (width, height), substrate_color_rgba)

        texture_type = base_material_settings.get("texture_type", "flat")
        grain_intensity = float(base_material_settings.get("grain_intensity", DEFAULT_GRAIN_INTENSITY))

        if texture_type == "hammered":
            if BUILDER_DEBUG: builder_logger.trace("🔨🎨✨ [LAYER] Applying hammered texture.")
            hammered_texture = SubstrateFactory.generate_hammered(width, height, grain_intensity, scale_factor=scale_factor).convert("RGBA")
            panel_image = ImageChops.multiply(panel_image, hammered_texture)
        elif texture_type == "wrinkle":
            if BUILDER_DEBUG: builder_logger.trace("🌀🎨✨ [LAYER] Applying wrinkle noise texture.")
            # Wrinkle noise at target res
            noise_w, noise_h = int(width * scale_factor), int(height * scale_factor)
            wrinkle_texture = Image.effect_noise((noise_w, noise_h), sigma=WRINKLE_SIGMA).convert("RGBA")
            if scale_factor > 1.0:
                wrinkle_texture = wrinkle_texture.resize((width, height), resample=Image.LANCZOS)
            panel_image = ImageChops.multiply(panel_image, wrinkle_texture)
        elif texture_type == "crosshatch":
            if BUILDER_DEBUG: builder_logger.trace("🧺🎨✨ [LAYER] Weaving crosshatch streaks.")
            horizontal_streaks = SubstrateFactory.generate_streaks(width, height, vertical=False, sigma=STREAK_SIGMA_CROSSHATCH, scale_factor=scale_factor)
            vertical_streaks = SubstrateFactory.generate_streaks(width, height, vertical=True, sigma=STREAK_SIGMA_CROSSHATCH, scale_factor=scale_factor)
            crosshatch_weave = ImageChops.multiply(horizontal_streaks, vertical_streaks).convert("RGBA")
            panel_image = ImageChops.multiply(panel_image, crosshatch_weave)
        elif texture_type == "enamel":
            if BUILDER_DEBUG: builder_logger.trace("✨🎨✨ [LAYER] Applying enamel peel texture.")
            # Adjusted resize factor based on scale
            adj_enamel_factor = max(1, ENAMEL_RESIZE_FACTOR / scale_factor)
            peel_texture = Image.effect_noise((int(width // adj_enamel_factor), int(height // adj_enamel_factor)), sigma=STREAK_SIGMA_CROSSHATCH).resize((width, height), Image.BICUBIC).convert("RGBA")
            panel_image = ImageChops.soft_light(panel_image, peel_texture)
        else:
            streak_sigma = STREAK_SIGMA_BRUSHED if texture_type == "brushed" else STREAK_SIGMA_DEFAULT
            if BUILDER_DEBUG: builder_logger.trace(f"🖌️🎨✨ [LAYER] Applying {texture_type} streak texture.")
            is_vertical = (base_material_settings.get("grain_direction") == "vertical")
            directional_streaks = SubstrateFactory.generate_streaks(width, height, vertical=is_vertical, sigma=streak_sigma, scale_factor=scale_factor).convert("RGBA")
            panel_image = ImageChops.multiply(panel_image, directional_streaks)

        # --- Layer 2: The Paint Layer ---
        paint_color_rgb = PanelUtils.hex_to_rgb(paint_layer_settings.get("color", "#4a5a6a"))
        paint_opacity = float(paint_layer_settings.get("opacity", DEFAULT_PAINT_OPACITY))
        if BUILDER_DEBUG: builder_logger.trace(f"🎨🖌️🌈 [LAYER] 2. Paint: {paint_layer_settings.get('color')} (Opacity: {paint_opacity})")
        paint_mask_image = Image.new('L', (width, height), MAX_OPACITY_VALUE)

        if edge_wear_settings.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🔪🎨✨ [LAYER] Etching edge wear scratches.")
            scratch_depth_limit = int(edge_wear_settings.get("scratch_depth", DEFAULT_EDGE_SCRATCH_DEPTH))
            edge_scratch_mask = Image.new('L', (width, height), 0)
            edge_scratch_draw = ImageDraw.Draw(edge_scratch_mask)
            edge_scratch_count = int(edge_wear_settings.get("scratch_intensity", DEFAULT_EDGE_SCRATCH_INTENSITY) * EDGE_SCRATCH_COUNT_MULTIPLIER)
            for _ in range(edge_scratch_count):
                selected_edge = random.choice(["top", "bottom", "left", "right"])
                if selected_edge == "top":
                    start_x, start_y = random.randint(0, width - 1), 0
                    end_x, end_y = start_x + random.randint(-EDGE_SCRATCH_OFFSET_RANGE, EDGE_SCRATCH_OFFSET_RANGE), random.randint(0, scratch_depth_limit)
                elif selected_edge == "bottom":
                    start_x, start_y = random.randint(0, width - 1), height - 1
                    end_x, end_y = start_x + random.randint(-EDGE_SCRATCH_OFFSET_RANGE, EDGE_SCRATCH_OFFSET_RANGE), height - 1 - random.randint(0, scratch_depth_limit)
                elif selected_edge == "left":
                    start_x, start_y = 0, random.randint(0, height - 1)
                    end_x, end_y = random.randint(0, scratch_depth_limit), start_y + random.randint(-EDGE_SCRATCH_OFFSET_RANGE, EDGE_SCRATCH_OFFSET_RANGE)
                else:
                    start_x, start_y = width - 1, random.randint(0, height - 1)
                    end_x, end_y = width - 1 - random.randint(0, scratch_depth_limit), start_y + random.randint(-EDGE_SCRATCH_OFFSET_RANGE, EDGE_SCRATCH_OFFSET_RANGE)
                edge_scratch_draw.line((start_x, start_y, end_x, end_y), fill=MAX_OPACITY_VALUE, width=random.randint(1, 2))
            paint_mask_image = ImageChops.subtract(paint_mask_image, edge_scratch_mask)

        surface_scratch_count = int(panel_scratch_settings.get("count", 0))
        if surface_scratch_count > 0 and panel_scratch_settings.get("reveals_substrate", False):
            if BUILDER_DEBUG: builder_logger.trace("🗡️🎨✨ [LAYER] Carving deep substrate-revealing scratches.")
            substrate_reveal_mask = Image.new('L', (width, height), 0)
            substrate_reveal_draw = ImageDraw.Draw(substrate_reveal_mask)
            for _ in range(surface_scratch_count):
                start_x, start_y = random.randint(0, width - 1), random.randint(0, height - 1)
                scratch_length = random.randint(int(panel_scratch_settings.get("min_length_px", DEFAULT_MIN_SCRATCH_LENGTH)), int(panel_scratch_settings.get("max_length_px", DEFAULT_MAX_SCRATCH_LENGTH)))
                scratch_angle = random.uniform(0, 2 * math.pi)
                end_x, end_y = start_x + scratch_length * math.cos(scratch_angle), start_y + scratch_length * math.sin(scratch_angle)
                substrate_reveal_draw.line((start_x, start_y, end_x, end_y), fill=MAX_OPACITY_VALUE, width=int(panel_scratch_settings.get("width_px", DEFAULT_SCRATCH_WIDTH)))
            paint_mask_image = ImageChops.subtract(paint_mask_image, substrate_reveal_mask.filter(ImageFilter.GaussianBlur(SCRATCH_GAUSSIAN_BLUR_RADIUS)))

        if paint_opacity > 0:
            solid_paint_layer = Image.new('RGBA', (width, height), paint_color_rgb + (MAX_OPACITY_VALUE,))
            blended_paint_layer = Image.blend(panel_image, solid_paint_layer, max(0.0, min(1.0, paint_opacity)))
            panel_image = Image.composite(blended_paint_layer, panel_image, paint_mask_image)

        gradient_intensity = float(paint_layer_settings.get("gradient_intensity", DEFAULT_GRADIENT_INTENSITY))
        if gradient_intensity > 0:
            if BUILDER_DEBUG: builder_logger.trace("📐🎨✨ [LAYER] Applying linear lighting gradient.")
            lighting_gradient = VignetteLayer.generate_linear_gradient(width, height, gradient_intensity)
            panel_image = ImageChops.multiply(panel_image, lighting_gradient)

        # --- Layer 3: Studio Haze ---
        if haze_settings.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🌫️🎨✨ [LAYER] 3. Infusing warm studio haze.")
            haze_alpha = int(MAX_OPACITY_VALUE * float(haze_settings.get("intensity", DEFAULT_HAZE_INTENSITY)))
            studio_haze_layer = Image.new('RGBA', (width, height), STUDIO_HAZE_COLOR + (haze_alpha,))
            panel_image = ImageChops.multiply(panel_image, studio_haze_layer)

        # --- Layer 4: Rust ---
        if rust_settings.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🟠🎨✨ [LAYER] 4. Spawning rust oxidation spots.")
            rust_intensity = float(rust_settings.get("intensity", 0.5))
            rust_layer_image = RustLayer.generate_rust_spots(width, height, rust_intensity)
            panel_image = Image.alpha_composite(panel_image, rust_layer_image)

        # --- Layer 5: Edge Fade ---
        vignette_intensity_value = float(edge_wear_settings.get("vignette_intensity", 0))
        if edge_wear_settings.get("enabled", False) and vignette_intensity_value > 0:
            if BUILDER_DEBUG: builder_logger.trace("🔳🎨✨ [LAYER] 5. Applying vignette edge fade.")
            fade_depth_limit = min(int(edge_wear_settings.get("fade_depth", DEFAULT_FADE_DEPTH)), min(width, height) // 2)
            vignette_layer_image = VignetteLayer.generate_vignette(width, height, vignette_intensity_value, fade_depth_limit)
            panel_image = ImageChops.multiply(panel_image, vignette_layer_image)

        # --- Layer 6: Scratches ---
        if int(panel_scratch_settings.get("count", 0)) > 0:
            if BUILDER_DEBUG: builder_logger.trace("🖊️🎨✨ [LAYER] 6. Adding surface micro-scratches.")
            scratch_layer_image = ScratchLayer.generate_scratches(width, height, panel_scratch_settings)
            panel_image = Image.alpha_composite(panel_image, scratch_layer_image)

        # --- Layer 7: Stains ---
        if int(grime_settings.get("stain_count", 0)) > 0:
            if BUILDER_DEBUG: builder_logger.trace("☕🎨✨ [LAYER] 7. Adding grease and coffee stains.")
            stains_layer_image = StainsLayer.generate_stains(width, height, grime_settings)
            panel_image = Image.alpha_composite(panel_image, stains_layer_image)

        # --- Layer 8: Details ---
        if screws_settings.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🔩🎨✨ [LAYER] 8. Drilling screws into the panel.")
            screws_layer_image = ScrewLayer.generate_screws(width, height, screws_settings, fold_settings)
            panel_image = Image.alpha_composite(panel_image, screws_layer_image)
        if fold_settings.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("📐🎨✨ [LAYER] 8. Folding metal creases.")
            fold_layer_image = MetalFoldLayer.generate_metal_fold(width, height, fold_settings)
            panel_image = Image.alpha_composite(panel_image, fold_layer_image)
        if dust_settings.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🌫️🎨✨ [LAYER] 8. Settling fine dust particles.")
            dust_intensity = float(dust_settings.get("intensity", 0.3))
            dust_layer_image = DustLayer.generate_dust(width, height, dust_intensity)
            panel_image = Image.alpha_composite(panel_image, dust_layer_image)

        blur_radius_value = float(settings.get("global_blur", DEFAULT_GLOBAL_BLUR))
        if blur_radius_value > 0:
            if BUILDER_DEBUG: builder_logger.trace(f"🌫️🎨✨ [FINAL] Applying global Gaussian blur: {blur_radius_value}")
            panel_image = panel_image.filter(ImageFilter.GaussianBlur(radius=blur_radius_value))

        if BUILDER_DEBUG: builder_logger.success("🎨🆗💾 [SUCCESS] Procedural panel generation complete. Saving to disk cache.")
        AssetCacheManager.save_to_cache("panel", width, height, configuration_data, panel_image)
        return panel_image

    @staticmethod
    def generate_tkinter_panel_image(width, height, configuration_data={}):
        """Generates a procedural panel and converts it to a Tkinter-compatible format."""
        try:
            pil_image = PanelGenerator.generate_procedural_panel(width, height, configuration_data)
            return ImageTk.PhotoImage(pil_image)
        except Exception:
            from oaLogging.Entry import vocal_capture
            vocal_capture("BUILDER", "Failed to generate Tkinter-compatible panel image.")
            return None
