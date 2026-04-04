# oaGuiManager/Tests/test_transparency.py
# Author: Gemini CLI
# Version: 20260404.1.3
#
# Description: Unit tests for transparency.py logic.

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiManager.Core.transparency.transparency import TransparencyConfig, BackgroundSlicer, TransparencyManager

class TestTransparency(unittest.TestCase):
    """Verifies that the transparency engine correctly parses config and slices backgrounds."""

    def setUp(self):
        """Build mock widgets and builder."""
        self.mock_widget = MagicMock(spec=tk.Widget)
        self.mock_widget.winfo_exists.return_value = True
        self.mock_widget.cget.return_value = "#ffffff"
        
        self.mock_canvas = MagicMock(spec=tk.Canvas)
        self.mock_canvas.winfo_exists.return_value = True
        self.mock_canvas.cget.return_value = "#ffffff"
        
        self.mock_builder = MagicMock()
        self.mock_builder.panel_bg_pil = MagicMock()
        self.mock_builder.panel_bg_pil.size = (1920, 1080)
        self.mock_builder.panel_bg_pil.crop.return_value = MagicMock()
        self.mock_builder.theme_colors = {"bg": "#2b2b2b"}

    def test_transparency_config_parsing(self):
        """OPERATE: Parse various configs. CHECK: Verify transparency detection logic."""
        # 1. Explicitly transparent
        config1 = {"transparent": True}
        bg, solid, trans = TransparencyConfig.parse_configuration(config1, self.mock_widget)
        self.assertTrue(trans, "Failed to detect explicit 'transparent': True")
        
        # 2. Structural type (e.g. OcaBlock from geometry.py)
        config2 = {"type": "OcaBlock"}
        bg, solid, trans = TransparencyConfig.parse_configuration(config2, self.mock_canvas)
        self.assertTrue(trans, "Failed to detect structural type 'OcaBlock'")
        
        # 3. Explicitly solid hex
        config3 = {"bg_color": "#ff0000"}
        bg, solid, trans = TransparencyConfig.parse_configuration(config3, self.mock_widget)
        self.assertEqual(bg, "#ff0000")
        self.assertTrue(solid)
        self.assertFalse(trans)

    @patch('PIL.ImageTk.PhotoImage')
    def test_background_slicer_perform_slice(self, mock_photo):
        """OPERATE: Perform slice. CHECK: Verify crop coordinates and image creation."""
        slicer = BackgroundSlicer(self.mock_widget, self.mock_canvas, self.mock_builder, "TestWidget")
        
        # Mock geometry
        self.mock_canvas.winfo_exists.return_value = True
        self.mock_canvas.winfo_width.return_value = 100
        self.mock_canvas.winfo_height.return_value = 50
        self.mock_canvas.winfo_rootx.return_value = 200
        self.mock_canvas.winfo_rooty.return_value = 100
        
        # Mock scroll root
        self.mock_builder.scroll_frame.winfo_rootx.return_value = 0
        self.mock_builder.scroll_frame.winfo_rooty.return_value = 0
        self.mock_builder.scroll_frame.winfo_exists.return_value = True
        
        # Ensure we don't have id collisions in coord_cache
        self.mock_builder._root_coord_cache = {}
        
        slicer.perform_slice()
        
        # Verify crop coordinates: (200, 100, 300, 150)
        self.mock_builder.panel_bg_pil.crop.assert_called_with((200, 100, 300, 150))

    def test_apply_transparency_registration(self):
        """OPERATE: Apply transparency. CHECK: Verify it's registered with the builder."""
        config = {"transparent": True}
        TransparencyManager.apply_transparency(self.mock_widget, self.mock_canvas, config, self.mock_builder)
        
        # Verify builder.register_for_slicing was called
        self.mock_builder.register_for_slicing.assert_called_once()

if __name__ == '__main__':
    unittest.main()
