# images/test_background_renderings.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import pytest
from PIL import Image, ImageChops

from oaGuiBackground.Interface.panels.panel_generator import PanelGenerator
from oaGuiBackground.Interface.panels.tiled_panel_generator import TiledPanelGenerator

# Test configurations representing the 6 sample styles identified in the 1_Demo directory
BACKGROUND_STYLES = [
    {
        "name": "Eggshell",
        "config": {
            "parameters": {
                "random_seed": 101,
                "base_material": {"color": "#f0ead6", "texture_type": "flat"},
                "paint_layer": {"color": "#ffffff", "opacity": 0.1}
            }
        }
    },
    {
        "name": "Heavy Rust",
        "config": {
            "parameters": {
                "random_seed": 102,
                "base_material": {"color": "#2a2a2a", "texture_type": "hammered"},
                "rust": {"enabled": True, "intensity": 0.8}
            }
        }
    },
    {
        "name": "Dusty Attic",
        "config": {
            "parameters": {
                "random_seed": 103,
                "base_material": {"color": "#444444", "texture_type": "wrinkle"},
                "dust": {"enabled": True, "intensity": 0.7}
            }
        }
    },
    {
        "name": "Oily Shop",
        "config": {
            "parameters": {
                "random_seed": 104,
                "base_material": {"color": "#1a1a1a", "texture_type": "brushed"},
                "grime": {"stain_count": 15, "opacity": 0.5}
            }
        }
    },
    {
        "name": "Subtle Wear",
        "config": {
            "parameters": {
                "random_seed": 105,
                "base_material": {"color": "#333333", "texture_type": "crosshatch"},
                "panel_scratches": {"count": 10, "intensity": 0.3, "reveals_substrate": True}
            }
        }
    },
    {
        "name": "Military Drab",
        "config": {
            "parameters": {
                "random_seed": 106,
                "base_material": {"color": "#4b5320", "texture_type": "enamel"},
                "paint_layer": {"color": "#4b5320", "opacity": 0.9},
                "edge_wear": {"enabled": True, "scratch_intensity": 0.6}
            }
        }
    }
]

@pytest.mark.parametrize("style", BACKGROUND_STYLES)
def test_background_rendering(style):
    """Verifies that the PanelGenerator can render each of the 6 sample styles."""
    width, height = 400, 300
    img = PanelGenerator.generate_procedural_panel(width, height, style["config"])
    assert isinstance(img, Image.Image)
    assert img.size == (width, height)
    assert img.mode == 'RGBA'

@pytest.mark.parametrize("style", BACKGROUND_STYLES)
def test_tiled_background_rendering(style):
    """Verifies that the TiledPanelGenerator can render each of the 6 sample styles."""
    width, height = 512, 512
    img = TiledPanelGenerator.generate_tiled(width, height, style["config"], tile_size=256)
    assert isinstance(img, Image.Image)
    assert img.size == (width, height)
    assert img.mode == 'RGBA'

@pytest.mark.parametrize("style", BACKGROUND_STYLES)
def test_rendering_consistency(style):
    """Verifies that Tiled and Standard rendering produce the same results for a fixed seed."""
    width, height = 256, 256

    # 1. Standard Render
    img_std = PanelGenerator.generate_procedural_panel(width, height, style["config"])

    # 2. Tiled Render
    img_tiled = TiledPanelGenerator.generate_tiled(width, height, style["config"], tile_size=128)

    # 3. Compare (they should be identical because Tiled currently just crops the full render)
    diff = ImageChops.difference(img_std, img_tiled)
    assert diff.getbbox() is None, f"Rendering inconsistency detected in style: {style['name']}"
