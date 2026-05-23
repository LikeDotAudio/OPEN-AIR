# oaGui/Methods/button_image_renderer.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles photorealistic rendering of button images using PIL.

from loguru import logger
from PIL import Image, ImageDraw, ImageTk

from oaGui.Methods.formatting.i18n_utils import get_text


class ButtonImageRenderer:
    """
    Handles photorealistic rendering of button images using PIL.
    """
    @staticmethod
    def create_button_image(width, height, text, is_active, is_hovered, is_pressed, config):
        """Creates a photorealistic button image."""
        width, height = max(1, int(width)), max(1, int(height))
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Determine colors from config
        bg_color = config.get("bg_color", "#1a1a1a")
        active_bg_color = config.get("active_bg_color", "#000000")
        active_color = config.get("active_color", "#FF9900")
        text_color = config.get("text_color", "#888888")
        active_text_color = config.get("active_text_color", "#1a1a1a")
        glow_intensity = config.get("glow_intensity", 1.0)
        corner_radius = config.get("corner_radius", 6)

        if is_active:
            bg = active_bg_color
            border = None
        else:
            bg = bg_color
            border = "#333333"

        if is_pressed:
            bg = "#000000"
            border = None

        # Draw Base Rounded Rect
        draw.rounded_rectangle([0, 0, width-1, height-1], corner_radius, fill=bg, outline=border, width=1)

        # Glow Effect if active
        if is_active and glow_intensity > 0:
            try:
                r_c = int(active_color[1:3], 16)
                g_c = int(active_color[3:5], 16)
                b_c = int(active_color[5:7], 16)

                center_x, center_y = width / 2, height / 2
                max_radius = min(width, height) * 0.8 * (glow_intensity / 10.0)
                num_steps = max(10, int(30 * (glow_intensity / 10.0)))

                for i in range(num_steps, 0, -1):
                    radius = (max_radius / num_steps) * i
                    alpha_factor = (1 - (i / (num_steps + 1)))**2
                    alpha = int(100 * alpha_factor * (glow_intensity / 10.0))

                    if alpha > 0:
                        draw.ellipse(
                            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                            fill=(r_c, g_c, b_c, alpha)
                        )
            except Exception as e:
                logger.error(f"ButtonImageRenderer: Failed to render radiating glow: {e}")

        # Draw Text
        try:
            display_text = get_text(text)
            draw.text((width / 2, height / 2), display_text,
                      fill=active_text_color if is_active else text_color, anchor="mm")
        except Exception as e:
            logger.error(f"ButtonImageRenderer: Error drawing button text: {e}")

        return ImageTk.PhotoImage(image)
