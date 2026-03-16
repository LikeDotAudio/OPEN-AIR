from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageTk
import random
import math

# --- Imports for the new modular architecture ---
from .core.utils import PanelUtils
from .core.substrate_factory import SubstrateFactory
from .core.layer_rust import RustLayer
from .core.layer_vignette import VignetteLayer
from .core.layer_stains import StainsLayer
from .core.layer_dust import DustLayer
from .core.layer_scratches import ScratchLayer
from .core.layer_screws import ScrewLayer
from .core.layer_metal_fold import MetalFoldLayer

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import builder_logger
from managers.configini.config_reader import Config
from managers.Display.factory.asset_cache import AssetCacheManager

class PanelGenerator:
    """
    Advanced Procedural Panel Generator (Modular Version).
    Orchestrates specialized layer modules to simulate physical materials.
    """

    @staticmethod
    def generate_panel(width, height, config={}):
        """
        Generates a PIL Image based on detailed physical parameters.
        Includes disk caching to prevent redundant generation.
        """
        # --- 0. Check Cache First ---
        if BUILDER_DEBUG: builder_logger.trace(f"📦🔍✨ [CACHE] Checking for procedural panel in cache: {width}x{height}")
        cached_img = AssetCacheManager.load_from_cache("panel", width, height, config)
        if cached_img:
            if BUILDER_DEBUG: builder_logger.debug(f"📦🆗✅ [CACHE] Retaining procedural panel from disk cache.")
            return cached_img

        # --- 1. Extract Parameters ---
        params = config.get("parameters", config)
        seed = params.get("random_seed")
        if not seed:
            seed = random.randint(1, 1000000)
        random.seed(seed)
        
        if BUILDER_DEBUG: builder_logger.info(f"🎨🏗️🌀 [BUILDER] Generating NEW Procedural Panel ({width}x{height}) Seed: {seed}")

        # --- 2. Layer Configs ---
        base_cfg = params.get("base_material", {})
        paint_cfg = params.get("paint_layer", {})
        edge_cfg = params.get("edge_wear", {"enabled": False}) 
        panel_scratch_cfg = params.get("panel_scratches", params.get("scratches", {"count": 0}))
        grime_cfg = params.get("grime", {"stain_count": 0}) 
        rust_cfg = params.get("rust", {"enabled": False})      
        dust_cfg = params.get("dust", {"enabled": False, "intensity": 0.3})
        screws_cfg = params.get("screws", {"enabled": False})
        fold_cfg = params.get("metal_fold", {"enabled": False})
        haze_cfg = params.get("studio_haze", {"enabled": False})

        # --- Layer 1: The Substrate (The Metal Panel) ---
        sub_color = base_cfg.get("color", "#2a2a2a")
        if BUILDER_DEBUG: builder_logger.trace(f"🎨🖌️🔳 [LAYER] 1. Substrate: {sub_color}")
        sub_color_rgba = PanelUtils.hex_to_rgba(sub_color)
        img = Image.new('RGBA', (width, height), sub_color_rgba)
        
        texture_type = base_cfg.get("texture_type", "flat")
        grain_int = float(base_cfg.get("grain_intensity", 0.15))
        
        if texture_type == "hammered":
            if BUILDER_DEBUG: builder_logger.trace("🔨🎨✨ [LAYER] Applying hammered texture.")
            hammered = SubstrateFactory.generate_hammered(width, height, grain_int).convert("RGBA")
            img = ImageChops.multiply(img, hammered)
        elif texture_type == "wrinkle":
            if BUILDER_DEBUG: builder_logger.trace("🌀🎨✨ [LAYER] Applying wrinkle noise texture.")
            wrinkle = Image.effect_noise((width, height), sigma=80).convert("RGBA")
            img = ImageChops.multiply(img, wrinkle)
        elif texture_type == "crosshatch":
            if BUILDER_DEBUG: builder_logger.trace("🧺🎨✨ [LAYER] Weaving crosshatch streaks.")
            h = SubstrateFactory.generate_streaks(width, height, vertical=False, sigma=10)
            v = SubstrateFactory.generate_streaks(width, height, vertical=True, sigma=10)
            weave = ImageChops.multiply(h, v).convert("RGBA")
            img = ImageChops.multiply(img, weave)
        elif texture_type == "enamel":
            if BUILDER_DEBUG: builder_logger.trace("✨🎨✨ [LAYER] Applying enamel peel texture.")
            peel = Image.effect_noise((width // 4, height // 4), sigma=10).resize((width, height), Image.BICUBIC).convert("RGBA")
            img = ImageChops.soft_light(img, peel)
        else:
            sigma = 20 if texture_type == "brushed" else 5
            if BUILDER_DEBUG: builder_logger.trace(f"🖌️🎨✨ [LAYER] Applying {texture_type} streak texture.")
            streaks = SubstrateFactory.generate_streaks(width, height, vertical=(base_cfg.get("grain_direction") == "vertical"), sigma=sigma).convert("RGBA")
            img = ImageChops.multiply(img, streaks)

        # --- Layer 2: The Paint Layer ---
        paint_color = PanelUtils.hex_to_rgb(paint_cfg.get("color", "#4a5a6a"))
        paint_opacity = float(paint_cfg.get("opacity", 0.0))
        if BUILDER_DEBUG: builder_logger.trace(f"🎨🖌️🌈 [LAYER] 2. Paint: {paint_cfg.get('color')} (Opacity: {paint_opacity})")
        paint_mask = Image.new('L', (width, height), 255)
        
        if edge_cfg.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🔪🎨✨ [LAYER] Etching edge wear scratches.")
            s_depth = int(edge_cfg.get("scratch_depth", 30))
            s_mask = Image.new('L', (width, height), 0)
            draw_edge_s = ImageDraw.Draw(s_mask)
            for _ in range(int(edge_cfg.get("scratch_intensity", 0.5) * 50)):
                edge = random.choice(["top", "bottom", "left", "right"])
                if edge == "top": 
                    x1, y1 = random.randint(0, width - 1), 0
                    x2, y2 = x1 + random.randint(-20, 20), random.randint(0, s_depth)
                elif edge == "bottom":
                    x1, y1 = random.randint(0, width - 1), height - 1
                    x2, y2 = x1 + random.randint(-20, 20), height - 1 - random.randint(0, s_depth)
                elif edge == "left":
                    x1, y1 = 0, random.randint(0, height - 1)
                    x2, y2 = random.randint(0, s_depth), y1 + random.randint(-20, 20)
                else:
                    x1, y1 = width - 1, random.randint(0, height - 1)
                    x2, y2 = width - 1 - random.randint(0, s_depth), y1 + random.randint(-20, 20)
                draw_edge_s.line((x1, y1, x2, y2), fill=255, width=random.randint(1, 2))
            paint_mask = ImageChops.subtract(paint_mask, s_mask)

        if int(panel_scratch_cfg.get("count", 0)) > 0 and panel_scratch_cfg.get("reveals_substrate", False):
            if BUILDER_DEBUG: builder_logger.trace("🗡️🎨✨ [LAYER] Carving deep substrate-revealing scratches.")
            ps_mask = Image.new('L', (width, height), 0)
            ps_draw = ImageDraw.Draw(ps_mask)
            for _ in range(int(panel_scratch_cfg.get("count", 0))):
                x1, y1 = random.randint(0, width - 1), random.randint(0, height - 1)
                length = random.randint(int(panel_scratch_cfg.get("min_length_px", 20)), int(panel_scratch_cfg.get("max_length_px", 150)))
                angle = random.uniform(0, 2 * math.pi)
                x2, y2 = x1 + length * math.cos(angle), y1 + length * math.sin(angle)
                ps_draw.line((x1, y1, x2, y2), fill=255, width=int(panel_scratch_cfg.get("width_px", 1)))
            paint_mask = ImageChops.subtract(paint_mask, ps_mask.filter(ImageFilter.GaussianBlur(1)))

        if paint_opacity > 0:
            solid_paint = Image.new('RGBA', (width, height), paint_color + (255,))
            blended_paint = Image.blend(img, solid_paint, max(0.0, min(1.0, paint_opacity)))
            img = Image.composite(blended_paint, img, paint_mask)

        grad_int = float(paint_cfg.get("gradient_intensity", 0.2))
        if grad_int > 0:
            if BUILDER_DEBUG: builder_logger.trace("📐🎨✨ [LAYER] Applying linear lighting gradient.")
            img = ImageChops.multiply(img, VignetteLayer.generate_linear_gradient(width, height, grad_int))

        # --- Layer 3: Studio Haze ---
        if haze_cfg.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🌫️🎨✨ [LAYER] 3. Infusing warm studio haze.")
            haze = Image.new('RGBA', (width, height), (180, 140, 50, int(255 * float(haze_cfg.get("intensity", 0.15)))))
            img = ImageChops.multiply(img, haze)

        # --- Layer 4: Rust ---
        if rust_cfg.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🟠🎨✨ [LAYER] 4. Spawning rust oxidation spots.")
            img = Image.alpha_composite(img, RustLayer.generate_rust_spots(width, height, float(rust_cfg.get("intensity", 0.5))))

        # --- Layer 5: Edge Fade ---
        if edge_cfg.get("enabled", False) and float(edge_cfg.get("vignette_intensity", 0)) > 0:
            if BUILDER_DEBUG: builder_logger.trace("🔳🎨✨ [LAYER] 5. Applying vignette edge fade.")
            f_depth = min(int(edge_cfg.get("fade_depth", 110)), min(width, height) // 2)
            vignette = VignetteLayer.generate_vignette(width, height, float(edge_cfg.get("vignette_intensity", 0.5)), f_depth)
            img = ImageChops.multiply(img, vignette)

        # --- Layer 6: Scratches ---
        if int(panel_scratch_cfg.get("count", 0)) > 0:
            if BUILDER_DEBUG: builder_logger.trace("🖊️🎨✨ [LAYER] 6. Adding surface micro-scratches.")
            img = Image.alpha_composite(img, ScratchLayer.generate_scratches(width, height, panel_scratch_cfg))

        # --- Layer 7: Stains ---
        if int(grime_cfg.get("stain_count", 0)) > 0:
            if BUILDER_DEBUG: builder_logger.trace("☕🎨✨ [LAYER] 7. Adding grease and coffee stains.")
            img = Image.alpha_composite(img, StainsLayer.generate_stains(width, height, grime_cfg))

        # --- Layer 8: Details ---
        if screws_cfg.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🔩🎨✨ [LAYER] 8. Drilling screws into the panel.")
            img = Image.alpha_composite(img, ScrewLayer.generate_screws(width, height, screws_cfg, fold_cfg))
        if fold_cfg.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("📐🎨✨ [LAYER] 8. Folding metal creases.")
            img = Image.alpha_composite(img, MetalFoldLayer.generate_metal_fold(width, height, fold_cfg))
        if dust_cfg.get("enabled", False):
            if BUILDER_DEBUG: builder_logger.trace("🌫️🎨✨ [LAYER] 8. Settling fine dust particles.")
            img = Image.alpha_composite(img, DustLayer.generate_dust(width, height, float(dust_cfg.get("intensity", 0.3))))

        blur_amount = float(params.get("global_blur", 0.0))
        if blur_amount > 0:
            if BUILDER_DEBUG: builder_logger.trace(f"🌫️🎨✨ [FINAL] Applying global Gaussian blur: {blur_amount}")
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_amount))

        if BUILDER_DEBUG: builder_logger.success(f"🎨🆗💾 [SUCCESS] Procedural panel generation complete. Saving to disk cache.")
        AssetCacheManager.save_to_cache("panel", width, height, config, img)
        return img

    @staticmethod
    def create_tk_image(width, height, config={}):
        try:
            pil_img = PanelGenerator.generate_panel(width, height, config)
            return ImageTk.PhotoImage(pil_img)
        except: return None
