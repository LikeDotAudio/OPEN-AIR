# oaGuiManager/Tests/test_button_canvas_base.py
# Author: Gemini CLI
# Version: 20260404.1.1
#
# Description: Unit tests for button_canvas_base.py

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiManager.Core.factory.button_canvas_base import CanvasButton


class TestCanvasButton(unittest.TestCase):
    """Verifies that the photorealistic canvas button behaves correctly."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        """Build a mock parent and widget."""
        self.mock_command = MagicMock()
        # ⚡ FIX: Use a real tk.Frame as the parent, not the root Tk window.
        # This resolves an attribute error when the canvas tries to access parent properties.
        parent = tk.Frame(self.root)
        self.button = CanvasButton(parent, text="Test", command=self.mock_command)

        # Mock canvas methods used in drawing to avoid actual Tcl calls during test
        self.button.create_image = MagicMock()
        self.button.delete = MagicMock()
        self.button.tag_lower = MagicMock()
        # Mock find_all to return empty list
        self.button.find_all = MagicMock(return_value=[])
        # Mock geometry
        self.button.winfo_width = MagicMock(return_value=100)
        self.button.winfo_height = MagicMock(return_value=50)

    def test_state_changes(self):
        """OPERATE: Trigger state changes. CHECK: Verify visual update signals."""
        with patch.object(self.button, '_draw') as mock_draw:
            self.button.set_active(True)
            self.assertTrue(self.button.is_active)
            mock_draw.assert_called_once()

            self.button.set_text("NewText")
            self.assertEqual(self.button.text, "NewText")
            self.assertEqual(mock_draw.call_count, 2)

    def test_interaction_events(self):
        """OPERATE: Trigger mouse events. CHECK: Verify internal state updates."""
        with patch.object(self.button, '_draw') as mock_draw:
            # Hover
            self.button._on_enter(MagicMock())
            self.assertTrue(self.button.is_hovered)

            # Press
            self.button._on_press(MagicMock())
            self.assertTrue(self.button.is_pressed)

            # Release calls command
            self.button._on_release(MagicMock())
            self.assertFalse(self.button.is_pressed)
            self.mock_command.assert_called()

    @patch('PIL.Image.new')
    @patch('PIL.ImageDraw.Draw')
    @patch('PIL.ImageTk.PhotoImage')
    def test_draw_calls_pil(self, mock_photo, mock_draw, mock_new):
        """OPERATE: Trigger draw. CHECK: Verify PIL image creation."""
        # Force a draw
        self.button._draw()

        # Verify PIL was used to create the image
        mock_new.assert_called_with("RGBA", (100, 50), (0, 0, 0, 0))
        mock_draw.assert_called()
        self.button.create_image.assert_called()

if __name__ == '__main__':
    unittest.main()
