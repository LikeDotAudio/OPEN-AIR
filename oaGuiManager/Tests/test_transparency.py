# /home/anthony/Documents/OPEN-AIR/oaGuiManager/Tests/test_transparency.py
# Author: Gemini CLI
# Version: 20260404.1.1
# Description: Unit tests for the oaGuiManager transparency module.

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk

# Mocking external dependencies and project-specific constants/classes
class MockConstants:
    MIN_WIDGET_DIMENSION = 10
    PRE_LAYOUT_DIMENSION_LIMIT = 50
    JITTER_THRESHOLD_PIXELS = 5
    CENTER_SAMPLE_DIVISOR = 2
    STRUCTURAL_WIDGET_TYPES = ["frame", "toplevel", "canvas"]
    THEME_BACKGROUND_COLORS = ["transparent", "none", "match_theme", "#333333", "#2b2b2b"]
    DEFAULT_THEME_BACKGROUND = "#2b2b2b"

# Mocking matrix_log for testing purposes
def mock_matrix_log(*args, **kwargs):
    pass

# Mocking PIL components
class MockPhotoImage:
    def __init__(self, image):
        self.image = image
        self.size = (100, 100)

class MockImageCrop:
    def crop(self, box):
        return MockImageCrop()

class MockImage:
    size = (200, 200)
    def crop(self, box):
        return MockImageCrop()
    def getpixel(self, xy):
        return (128, 128, 128)

MockPILImage = MagicMock()
MockPILImage.open.return_value = MockImage()
MockPILImage.Image = MockImage

# --- Import the actual code to be tested ---
from oaGuiManager.Core.transparency import TransparencyConfig, BackgroundSlicer, TransparencyManager

# Target module for patching
TARGET_MODULE = 'oaGuiManager.Core.transparency.transparency'

@patch(f'{TARGET_MODULE}.STRUCTURAL_WIDGET_TYPES', MockConstants.STRUCTURAL_WIDGET_TYPES)
@patch(f'{TARGET_MODULE}.THEME_BACKGROUND_COLORS', MockConstants.THEME_BACKGROUND_COLORS)
@patch(f'{TARGET_MODULE}.DEFAULT_THEME_BACKGROUND', MockConstants.DEFAULT_THEME_BACKGROUND)
@patch(f'{TARGET_MODULE}.PRE_LAYOUT_DIMENSION_LIMIT', MockConstants.PRE_LAYOUT_DIMENSION_LIMIT)
@patch(f'{TARGET_MODULE}.JITTER_THRESHOLD_PIXELS', MockConstants.JITTER_THRESHOLD_PIXELS)
@patch(f'{TARGET_MODULE}.CENTER_SAMPLE_DIVISOR', MockConstants.CENTER_SAMPLE_DIVISOR)
@patch(f'{TARGET_MODULE}.matrix_log', mock_matrix_log)
@patch('PIL.ImageTk.PhotoImage', MockPhotoImage)
@patch('PIL.Image', MockPILImage)
class TestTransparencyManager(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        self.mock_widget = MagicMock(spec=tk.Widget)
        self.mock_widget.winfo_exists.return_value = True
        self.mock_widget.cget.side_effect = lambda key: "#ffffff" if key == "bg" else ""
        self.mock_widget.configure = MagicMock()
        self.mock_widget.winfo_rootx.return_value = 100
        self.mock_widget.winfo_rooty.return_value = 100
        self.mock_widget.winfo_width.return_value = 300
        self.mock_widget.winfo_height.return_value = 300
        self.mock_widget.path = "mock_widget_path"

        self.mock_canvas = MagicMock(spec=tk.Canvas)
        self.mock_canvas.winfo_exists.return_value = True
        self.mock_canvas.cget.side_effect = lambda key: "#ffffff" if key == "bg" else ""
        self.mock_canvas.configure = MagicMock()
        self.mock_canvas.winfo_rootx.return_value = 100
        self.mock_canvas.winfo_rooty.return_value = 100
        self.mock_canvas.winfo_width.return_value = 300
        self.mock_canvas.winfo_height.return_value = 300
        self.mock_canvas.delete = MagicMock()
        self.mock_canvas.create_image = MagicMock()
        self.mock_canvas.tag_lower = MagicMock()

        self.mock_builder = MagicMock()
        self.mock_builder.panel_bg_pil = MockImage()
        self.mock_builder.theme_colors = {"bg": "#2b2b2b"}
        self.mock_builder._root_coord_cache = {}
        self.mock_builder.register_for_slicing = MagicMock()

        self.mock_configuration = {}
        self.widget_name = "MockWidget"

    def test_transparency_config_parse_background_color(self):
        """Test parsing various background color configurations."""
        config1 = {"bg_color": "#ff0000"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config1, self.mock_widget)
        self.assertEqual(bg, "#ff0000")
        self.assertTrue(solid)
        self.assertFalse(transparent)

        config2 = {"bg": "blue"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config2, self.mock_widget)
        self.assertEqual(bg, "blue")
        self.assertTrue(solid)
        self.assertFalse(transparent)

        config3 = {"style": {"background_color": "green"}}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config3, self.mock_widget)
        self.assertEqual(bg, "green")
        self.assertTrue(solid)
        self.assertFalse(transparent)

        config4 = {"background_color": None}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config4, self.mock_widget)
        self.assertEqual(bg, "")
        self.assertFalse(solid)
        self.assertFalse(transparent)

    def test_transparency_config_parse_transparent_values(self):
        """Test parsing configurations explicitly marked as transparent."""
        config_transparent_true = {"transparent": True}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_transparent_true, self.mock_widget)
        self.assertEqual(bg, "")
        self.assertFalse(solid)
        self.assertTrue(transparent)

        config_transparent_string = {"bg_color": "transparent"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_transparent_string, self.mock_widget)
        self.assertEqual(bg, "transparent")
        self.assertFalse(solid)
        self.assertTrue(transparent)

        config_match_theme = {"bg_color": "match_theme"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_match_theme, self.mock_widget)
        self.assertEqual(bg, "match_theme")
        self.assertFalse(solid)
        self.assertTrue(transparent)

        config_none = {"bg_color": "none"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_none, self.mock_widget)
        self.assertEqual(bg, "none")
        self.assertFalse(solid)
        self.assertTrue(transparent)

    def test_transparency_config_parse_structural_types(self):
        """Test transparency detection based on structural widget types."""
        config_structural = {"type": "canvas"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_structural, self.mock_canvas)
        self.assertEqual(bg, "")
        self.assertFalse(solid)
        self.assertTrue(transparent)

        config_structural_other = {"widget_type": "frame"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_structural_other, self.mock_widget)
        self.assertEqual(bg, "")
        self.assertFalse(solid)
        self.assertTrue(transparent)

    def test_transparency_config_parse_explicitly_solid(self):
        """Test identification of explicitly solid colors."""
        config_solid_hex = {"bg_color": "#123456"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_solid_hex, self.mock_widget)
        self.assertEqual(bg, "#123456")
        self.assertTrue(solid)
        self.assertFalse(transparent)

        config_solid_named_not_theme = {"bg_color": "red"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_solid_named_not_theme, self.mock_widget)
        self.assertEqual(bg, "red")
        self.assertTrue(solid)
        self.assertFalse(transparent)

        config_solid_theme_color = {"bg_color": "#333333"}
        bg, solid, transparent = TransparencyConfig.parse_configuration(config_solid_theme_color, self.mock_widget)
        self.assertEqual(bg, "#333333")
        self.assertFalse(solid)
        self.assertFalse(transparent)

    @patch.object(TransparencyManager, '_register_widget_for_slicing')
    def test_transparency_manager_apply_transparency_calls_register(self, mock_register):
        """Test that apply_transparency correctly calls the registration method."""
        TransparencyManager.apply_transparency(self.mock_widget, self.mock_canvas, self.mock_configuration, self.mock_builder)
        mock_register.assert_called_once_with(self.mock_widget, self.mock_canvas, self.mock_configuration, self.mock_builder, self.mock_widget.path)

    @patch.object(TransparencyManager, '_handle_registration_failure')
    @patch.object(TransparencyManager, '_register_widget_for_slicing', side_effect=Exception("Mock registration error"))
    def test_transparency_manager_apply_transparency_handles_errors(self, mock_register, mock_handle_failure):
        """Test that apply_transparency handles exceptions during registration."""
        TransparencyManager.apply_transparency(self.mock_widget, self.mock_canvas, self.mock_configuration, self.mock_builder)
        mock_register.assert_called_once()
        mock_handle_failure.assert_called_once()

    def test_transparency_manager_cleanup(self):
        """Test that cleanup clears the slicing registry."""
        mock_builder = MagicMock()
        mock_builder._slicing_registry = MagicMock()
        TransparencyManager.cleanup(mock_builder)
        mock_builder._slicing_registry.clear.assert_called_once()

if __name__ == '__main__':
    unittest.main()
