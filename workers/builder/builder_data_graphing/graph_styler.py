# workers/builder/builder_data_graphing/graph_styler.py
from typing import Dict, Any

def apply_style(ax: object, fig: object, style_config: Dict[str, Any], theme: Dict[str, Any]):
    """
    Applies colors, grid visibility, and axis visibility.
    """
    bg_color = style_config.get('bg_color', 'match_theme')
    if bg_color == 'match_theme':
        bg_color = theme.get('background', '#FFFFFF')

    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    ax.grid(style_config.get('show_grid', True))
    
    toggle_axis(ax, style_config.get('show_x_axis', True), style_config.get('show_y_axis', True))

    if style_config.get('show_title', True):
        ax.set_title(style_config.get('title', ''), color=theme.get('text', 'black'))
    else:
        ax.set_title('')

def toggle_grid(ax: object, visible: bool):
    """Toggles the grid visibility."""
    ax.grid(visible)

def toggle_axis(ax: object, x_visible: bool, y_visible: bool):
    """Toggles the visibility of x and y axes."""
    ax.get_xaxis().set_visible(x_visible)
    ax.get_yaxis().set_visible(y_visible)

def get_theme_style(theme_name: str) -> Dict[str, Any]:
    # In a real application, this would load from a style file.
    # For now, we'll use a hardcoded default.
    if theme_name == 'dark':
        return {
            'background': 'black',
            'text': 'white',
            'grid': 'darkgrey'
        }
    return {
        'background': 'white',
        'text': 'black',
        'grid': 'lightgrey'
    }