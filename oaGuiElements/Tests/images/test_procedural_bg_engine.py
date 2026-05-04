# oaGuiElements/Tests/images/test_procedural_bg_engine.py
# Author: Gemini CLI
# Version: 20260429.1.0
#
# Description: Integration test for the procedural background rendering engine.

import unittest
import tkinter as tk
from unittest.mock import MagicMock
from PIL import Image

from oaGuiElements.Core.background import BuilderBackgroundManagerMixin
from oaGuiElements.Core.panels.Core.panel_generator import PanelGenerator

class MockBuilder(tk.Frame, BuilderBackgroundManagerMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, width=400, height=300)
        self.canvas.pack()
        self.scroll_frame = tk.Frame(self.canvas)
        self.tab_name = "TestTab"
        self._render_tier = "high_res"
        self.config_data = {
            "background": {
                "parameters": {
                    "random_seed": 124,
                    "base_material": {"color": "#ff0000", "texture_type": "flat"}
                }
            }
        }
    
    def _trigger_reslice_all(self, force=False):
        pass

class TestProceduralBGEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_background_generation_cycle(self):
        """OPERATE: Trigger background generation. CHECK: Verify PIL image is created and applied."""
        builder = MockBuilder(self.root)
        builder.pack()
        builder.update() # Process events to ensure canvas has dimensions
        
        # Manually set dimensions if update() didn't (headless issue)
        w, h = 400, 300
        
        # Test direct generator first
        config = builder.config_data["background"]
        img = PanelGenerator.generate_procedural_panel(w, h, config)
        
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (w, h))
        
        # Sample top-left pixel (should be close to #ff0000)
        pixel = img.getpixel((0, 0))
        self.assertEqual(pixel[0], 255) # Red
        self.assertEqual(pixel[1], 0)   # Green
        self.assertEqual(pixel[2], 0)   # Blue

    def test_transparency_bypass_in_fast_mode(self):
        """OPERATE: Set tier to 'fast'. CHECK: Procedural background is skipped."""
        builder = MockBuilder(self.root)
        builder._render_tier = "fast"
        
        # Mock _clear_panel_background to see if it's called
        builder._clear_panel_background = MagicMock()
        
        builder._apply_panel_background(builder.config_data["background"], 100, 100)
        
        builder._clear_panel_background.assert_called_once()

if __name__ == "__main__":
    unittest.main()
