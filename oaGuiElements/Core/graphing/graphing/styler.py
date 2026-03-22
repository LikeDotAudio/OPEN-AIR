# graphing/styler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: styler.py

from typing import Dict, Any
from loguru import logger
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

class GraphStyler:
    """Handles visual styling and theme application for graphs."""

    @staticmethod
    def apply(ax: object, fig: object, config: Dict[str, Any], theme: Dict[str, Any]):
        """
        Applies colors, grid visibility, and axis visibility.
        Pushes elements of styling from JSON to the plot.
        """
        builder_logger.debug(f"🔬🏗️📊 [GRAPH] styler: Applying visual styles.")

        # 1. Background & Transparency
        style_block = config.get("style", {})
        is_transparent = config.get("transparent", False)
        bg_color = style_block.get("background_color", style_block.get("bg_color", "match_theme"))

        if bg_color == "match_theme":
            resolved_bg = theme.get("background", "none")
            if resolved_bg == "none": is_transparent = True
            bg_color = resolved_bg
        elif bg_color in ["transparent", "none"]:
            bg_color = "none"
            is_transparent = True

        if is_transparent:
            # ⚡ INDUSTRIAL TRANSPARENCY: Use alpha 0 instead of set_visible(False)
            # to ensure the background is captured for blitting.
            fig.patch.set_facecolor((0, 0, 0, 0))
            ax.patch.set_facecolor((0, 0, 0, 0))
            fig.patch.set_visible(True)
            ax.patch.set_visible(True)
            try:
                fig.patch.set_alpha(0.0)
                ax.patch.set_alpha(0.0)
            except: pass
        else:
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            fig.patch.set_visible(True)
            ax.patch.set_visible(True)
            try:
                fig.patch.set_alpha(1.0)
                ax.patch.set_alpha(1.0)
            except: pass

        # 2. Axis & Grid
        axis_config = config.get("axis", {})
        show_grid = axis_config.get("show_grid", config.get("show_grid", True))
        grid_color = style_block.get("grid_color", theme.get("grid", "gray"))
        ax.grid(show_grid, color=grid_color)

        show_x = axis_config.get("show_x_axis", config.get("show_x_axis", True))
        show_y = axis_config.get("show_y_axis", config.get("show_y_axis", True))
        ax.get_xaxis().set_visible(show_x)
        ax.get_yaxis().set_visible(show_y)

        # 3. Specific Axis Details
        for name, axis in [("x", ax.get_xaxis()), ("y", ax.get_yaxis())]:
            a_conf = axis_config.get(name, {})
            if not a_conf: continue

            if "label" in a_conf:
                if name == "x": ax.set_xlabel(a_conf["label"], color=theme.get("text", "white"))
                else: ax.set_ylabel(a_conf["label"], color=theme.get("text", "white"))

            if "scale" in a_conf:
                if name == "x": ax.set_xscale(a_conf["scale"])
                else: ax.set_yscale(a_conf["scale"])

            if "color" in a_conf:
                axis.set_tick_params(colors=a_conf["color"])
                for spine in ax.spines.values(): spine.set_color(a_conf["color"])

            # Limits
            if "min" in a_conf and "max" in a_conf:
                if a_conf["min"] != "auto" and a_conf["max"] != "auto":
                    if name == "x": ax.set_xlim(float(a_conf["min"]), float(a_conf["max"]))
                    else: ax.set_ylim(float(a_conf["min"]), float(a_conf["max"]))

        # 4. Title
        title = config.get("title", "")
        if title and config.get("show_title", True):
            ax.set_title(title, color=style_block.get("title_color", theme.get("text", "white")))
        else:
            ax.set_title("")

    @staticmethod
    def get_theme_style(theme_name: str) -> Dict[str, Any]:
        if theme_name == "dark":
            return {"background": "none", "text": "white", "grid": "#444444"}
        return {"background": "none", "text": "black", "grid": "#cccccc"}
