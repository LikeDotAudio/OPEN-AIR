# builder_data_graphing/graph_styler.py
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
    """
    bg_color = style_config.get("bg_color", "match_theme")
    if bg_color == "match_theme":
        bg_color = theme.get("background", "#FFFFFF")

    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    ax.grid(style_config.get("show_grid", True))

    toggle_axis(
        ax, style_config.get("show_x_axis", True), style_config.get("show_y_axis", True)
    )

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
        return {"background": "black", "text": "white", "grid": "darkgrey"}
    return {"background": "white", "text": "black", "grid": "lightgrey"}