# data_graphing/graph_styler.py
#
# This module provides functions for applying visual styles and themes to Matplotlib graphs.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
from typing import Dict, Any
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory

from managers.configini.config_reader import Config

app_constants = Config.get_instance()


# Applies various style configurations to a Matplotlib figure and axes.
# This function sets background colors, toggles grid and axis visibility,
# and configures the plot title based on the provided style configuration and theme.
# Inputs:
#     ax (object): The Matplotlib axes object.
#     fig (object): The Matplotlib figure object.
#     style_config (Dict[str, Any]): A dictionary of style settings.
#     theme (Dict[str, Any]): A dictionary containing theme-specific color and text settings.
# Outputs:
#     None.
def apply_style(
    ax: object, fig: object, style_config: Dict[str, Any], theme: Dict[str, Any]
):
    """
    Applies colors, grid visibility, and axis visibility.
    Supports nested 'style' and 'axis' configurations.
    """
    if LOCAL_DEBUG: logger.debug(f"📊💹 graph_styler: Applying visual styles to axis.")
    # Resolve 'style' dictionary
    nested_style = style_config.get("style", {})
    
    bg_color = nested_style.get("bg_color", nested_style.get("background_color", style_config.get("bg_color", "match_theme")))
    
    # ⚡ Check for explicit transparency override
    is_transparent = style_config.get("transparent", False)
    
    if bg_color == "match_theme":
        resolved_bg = theme.get("background", "none")
        if resolved_bg == "none": is_transparent = True
        bg_color = resolved_bg
    elif bg_color == "transparent" or bg_color == "none":
        bg_color = "none"
        is_transparent = True

    # ⚡ Use RGBA (0,0,0,0) for transparency
    if is_transparent:
        fig.patch.set_facecolor((0, 0, 0, 0))
        ax.patch.set_facecolor((0, 0, 0, 0))
        fig.patch.set_visible(False)
        ax.patch.set_visible(False)
        try: ax.patch.set_alpha(0.0)
        except Exception as e: logger.trace(f"Error setting alpha 0.0: {e}")
    else:
        # Standard hex or named color
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        fig.patch.set_visible(True)
        ax.patch.set_visible(True)
        try: ax.patch.set_alpha(1.0)
        except Exception as e: logger.trace(f"Error setting alpha 1.0: {e}")

    # Resolve 'axis' dictionary
    axis_config = style_config.get("axis", {})
    
    # Grid
    show_grid = axis_config.get("show_grid", style_config.get("show_grid", True))
    grid_color = nested_style.get("grid_color", theme.get("grid", "gray"))
    ax.grid(show_grid, color=grid_color)

    # Axes Visibility
    show_x = axis_config.get("show_x_axis", style_config.get("show_x_axis", True))
    show_y = axis_config.get("show_y_axis", style_config.get("show_y_axis", True))
    toggle_axis(ax, show_x, show_y)

    # --- New: Specific Axis Configuration (x/y) ---
    for axis_name, axis_obj in [("x", ax.get_xaxis()), ("y", ax.get_yaxis())]:
        # get config for this axis (e.g. axis_config["x"])
        a_conf = axis_config.get(axis_name, {})
        if not a_conf:
            continue
            
        # Label
        label = a_conf.get("label")
        if label:
            if axis_name == "x": ax.set_xlabel(label, color=theme.get("text", "black"))
            else: ax.set_ylabel(label, color=theme.get("text", "black"))
            
        # Scale
        scale = a_conf.get("scale")
        if scale:
            if axis_name == "x": ax.set_xscale(scale)
            else: ax.set_yscale(scale)
            
        # Color (Ticks and Spines)
        color = a_conf.get("color")
        if color:
            axis_obj.set_tick_params(colors=color)
            # Set spine colors
            if axis_name == "x":
                ax.spines['bottom'].set_color(color)
                ax.spines['top'].set_color(color)
            else:
                ax.spines['left'].set_color(color)
                ax.spines['right'].set_color(color)

    # Limits (Min/Max)
    # We handle this separately to allow 'auto' or numeric values
    x_conf = axis_config.get("x", {})
    y_conf = axis_config.get("y", {})
    
    x_min = x_conf.get("min")
    x_max = x_conf.get("max")
    if x_min is not None and x_max is not None and x_min != "auto" and x_max != "auto":
         ax.set_xlim(float(x_min), float(x_max))
         
    y_min = y_conf.get("min")
    y_max = y_conf.get("max")
    if y_min is not None and y_max is not None and y_min != "auto" and y_max != "auto":
         ax.set_ylim(float(y_min), float(y_max))


    if style_config.get("show_title", True):
        ax.set_title(style_config.get("title", ""), color=theme.get("text", "black"))
    else:
        ax.set_title("")


# Toggles the visibility of the grid lines on a Matplotlib axes.
# Inputs:
#     ax (object): The Matplotlib axes object.
#     visible (bool): True to show the grid, False to hide it.
# Outputs:
#     None.
def toggle_grid(ax: object, visible: bool):
    """Toggles the grid visibility."""
    ax.grid(visible)


# Toggles the visibility of the x and y axes on a Matplotlib axes.
# Inputs:
#     ax (object): The Matplotlib axes object.
#     x_visible (bool): True to show the x-axis, False to hide it.
#     y_visible (bool): True to show the y-axis, False to hide it.
# Outputs:
#     None.
def toggle_axis(ax: object, x_visible: bool, y_visible: bool):
    """Toggles the visibility of x and y axes."""
    ax.get_xaxis().set_visible(x_visible)
    ax.get_yaxis().set_visible(y_visible)


# Retrieves a predefined theme style.
# In a full application, this would load themes from a dedicated style file.
# Currently, it provides hardcoded 'dark' and default 'light' themes.
# Inputs:
#     theme_name (str): The name of the theme to retrieve (e.g., 'dark').
# Outputs:
#     Dict[str, Any]: A dictionary containing color and text settings for the specified theme.
def get_theme_style(theme_name: str) -> Dict[str, Any]:
    # In a real application, this would load from a style file.
    # For now, we'll use a hardcoded default.
    if theme_name == "dark":
        return {"background": "none", "text": "white", "grid": "darkgrey"}
    return {"background": "none", "text": "black", "grid": "lightgrey"}