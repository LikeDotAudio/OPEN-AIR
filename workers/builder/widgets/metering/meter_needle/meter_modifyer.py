# workers/builder/meter_needle/meter_modifyer.py

import tkinter as tk
from workers.builder.widgets.metering.meter_needle.cosmetics.background import BezelBackground
from workers.builder.widgets.metering.meter_needle.cosmetics.lens import BezelLens
from workers.builder.widgets.metering.meter_needle.cosmetics.mask import BezelMask
from workers.builder.widgets.metering.meter_needle.cosmetics.bezel import BezelOverlay
from workers.builder.widgets.metering.meter_needle.cosmetics.label import BezelLabel
from workers.builder.widgets.metering.meter_needle.cosmetics.lighting_overlay import VintageLightingGenerator

class MeterModifier:
    """
    Applies cosmetic modifications (Bezels, Overlays) to a Needle Meter Canvas.
    Orchestrates specialized drawers for Background, Lighting, Masks, and Bezel Frames.
    """

    @staticmethod
    def draw_labels(canvas, cx, cy, cosmetics, current_value=None):
        """Draws configurable text labels on the meter face."""
        BezelLabel.draw(canvas, cx, cy, cosmetics, current_value)

    @staticmethod
    def draw_background_faceplate(canvas, cx, cy, w, h, cosmetics):
        """Draws the solid background shape behind the meter."""
        BezelBackground.draw(canvas, cx, cy, w, h, cosmetics)

    @staticmethod
    def draw_lighting_effects(canvas, cx, cy, w, h, cosmetics):
        """Legacy lighting - disabled in favor of draw_glass_layer"""
        pass

    @staticmethod
    def draw_glass_layer(canvas, cx, cy, w, h, cosmetics):
        """Draws the PIL-generated Glass/Glow overlay."""
        style_overrides = cosmetics.get("style_overrides", {})
        if not style_overrides.get("enable_lighting", True):
            return

        bezel_shape = style_overrides.get("bezel_shape", None)
        if not bezel_shape:
            return

        bezel_width = int(style_overrides.get("bezel_width", 12))
        
        # Get lighting config from cosmetics
        lighting_config = cosmetics.get("lighting", {})
        
        # Pass overlay style for hill shadow logic
        style_overrides = cosmetics.get("style_overrides", {})
        lighting_config["overlay_style"] = style_overrides.get("overlay_style", None)
        
        # Default glow color to scale label color if not provided
        if "color" not in lighting_config:
            lighting_config["color"] = cosmetics.get("colors", {}).get("scale_label", "#FFB450")

        # Cache key needs to include all lighting params
        config_hash = str(sorted(lighting_config.items()))
        cache_key = f"{bezel_shape}_{w}_{h}_{cx}_{cy}_{config_hash}"
        
        if not hasattr(canvas, "lighting_cache"):
            canvas.lighting_cache = {}
            
        if cache_key not in canvas.lighting_cache:
            img = VintageLightingGenerator.photo_image(
                w, h, bezel_shape, bezel_width, cx, cy, lighting_config
            )
            canvas.lighting_cache[cache_key] = img
            
        photo_image = canvas.lighting_cache[cache_key]
        if photo_image:
            # Place at 0,0 to cover the whole canvas
            canvas.create_image(0, 0, image=photo_image, anchor="nw", tags="nextgen_foreground")

    @staticmethod
    def draw_foreground_overlay(canvas, cx, cy, w, h, cosmetics):
        """Draws the aperture mask (bottom cover) and the bezel frame (top outline)."""
        # --- 0. Draw Chassis Mask (Crops needles/pivots to bezel) ---
        MeterModifier._draw_chassis_mask(canvas, cx, cy, w, h, cosmetics)

        # 1. Mask (Bottom cover / Aperture)
        BezelMask.draw(canvas, cx, cy, w, h, cosmetics)
        
        # 2. Bezel Frame (Top outline)
        BezelOverlay.draw(canvas, cx, cy, w, h, cosmetics)

    @staticmethod
    def _draw_chassis_mask(canvas, cx, cy, w, h, cosmetics):
        """
        Creates an inverted mask of the bezel and fills it with the panel texture.
        This hides anything drawn 'outside' the meter area (like pivots/tails).
        """
        # ⚡ INDUSTRIAL TRANSPARENCY: Require patina slice for masking
        if not hasattr(canvas, 'panel_bg_pil_slice') or not canvas.panel_bg_pil_slice:
            return

        style_overrides = cosmetics.get("style_overrides", {})
        bezel_shape = style_overrides.get("bezel_shape", None)
        if not bezel_shape:
            return

        line_width = int(style_overrides.get("bezel_width", 12))
        
        # Cache the masked image to avoid per-frame PIL ops
        # Use id(panel_bg_pil_slice) to detect background changes
        cache_key = f"chassis_mask_{w}_{h}_{cx}_{cy}_{bezel_shape}_{id(canvas.panel_bg_pil_slice)}"
        if not hasattr(canvas, 'chassis_mask_cache'):
            canvas.chassis_mask_cache = {}

        if cache_key not in canvas.chassis_mask_cache:
            from PIL import Image, ImageDraw, ImageTk
            # 1. Create a mask: White (255) is the chassis, Black (0) is the 'hole'
            mask = Image.new('L', (w, h), 255)
            draw_mask = ImageDraw.Draw(mask)
            
            # Use BezelGeometry to get the 'Hole' points
            from workers.builder.widgets.metering.meter_needle.cosmetics.geometry import BezelGeometry
            # Shrink slightly to ensure no gap between mask and bezel frame
            shrink_px = line_width / 2.0
            points, is_smooth = BezelGeometry.get_bezel_points(cx, cy, w, h, bezel_shape, line_width, shrink_px=shrink_px)
            
            if points:
                # Draw the hole (Black)
                draw_mask.polygon(points, fill=0)
            
            # 2. Extract the panel texture and apply the mask
            # The mask alpha will hide the 'hole' area
            chassis_img = canvas.panel_bg_pil_slice.copy().convert("RGBA")
            if chassis_img.size != (w, h):
                chassis_img = chassis_img.resize((w, h), Image.Resampling.LANCZOS)
            
            # Create final image with the mask applied to alpha
            # ⚡ OPTIMIZATION: putalpha uses mask directly
            chassis_img.putalpha(mask)
            
            canvas.chassis_mask_cache[cache_key] = ImageTk.PhotoImage(chassis_img)

        # 3. Draw onto background layer (above panel slice, but below needles)
        # Use tag 'nextgen_background' to match z-ordering logic in meter_needle.py
        mask_id = canvas.create_image(0, 0, image=canvas.chassis_mask_cache[cache_key], anchor="nw", tags="nextgen_background")
        # Ensure it's below needles but above the base patina slice
        canvas.tag_lower(mask_id)
        # If there's a base slice, make sure the mask is ABOVE it
        try: canvas.tag_raise(mask_id, "panel_bg_slice")
        except: pass

    