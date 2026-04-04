# oaGuiManager/Tests/test_gui_elements.py
# Author: Gemini CLI
# Version: 20260404.1.3
#
# Description: Unit tests for specific GUI elements and their creators.

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.buttons.button_toggle.button_toggle import BuilderButtonToggleCreator, ToggleButton

class TestGuiElements(unittest.TestCase):
    """Verifies that GUI elements from oaGuiElements are correctly constructed."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        """Build mock dependencies for widget construction."""
        self.mock_context = MagicMock()
        self.mock_context.state_mirror_engine = MagicMock()
        self.mock_context.subscriber_router = MagicMock()
        self.mock_context.base_mqtt_topic_from_path = "OPEN-AIR/mock"
        
        self.mock_builder = MagicMock()
        self.mock_builder._apply_transparency = MagicMock()

    def test_button_toggle_creation(self):
        """OPERATE: Use Creator to make a ToggleButton. CHECK: Verify it's initialized correctly."""
        config = {
            "label": "TestToggle",
            "path": "test/toggle",
            "width": 100,
            "height": 50,
            "options": {
                "ON": {"label_active": "ACTIVE", "selected": True}
            }
        }
        
        # We don't patch Canvas.__init__ here because we have a real root.
        # But we patch Canvas drawing methods to avoid Tcl errors in headless env.
        with patch('tkinter.Canvas.create_text'):
            with patch('oaGuiManager.Core.factory.button_canvas_base.CanvasButton._draw'):
                creator = BuilderButtonToggleCreator()
                widget = creator.make_button_toggle(self.root, config, context=self.mock_context)
                
                # Verify we got a Canvas container (because label is present)
                self.assertIsInstance(widget, tk.Canvas)
                
                widget.destroy()

    def test_toggle_button_logic(self):
        """OPERATE: Toggle the button. CHECK: Verify state and variable updates."""
        config = {"label": "Toggle", "path": "path"}
        
        with patch('oaGuiManager.Core.factory.button_canvas_base.CanvasButton._draw'):
            # Create the button directly
            btn = ToggleButton(
                self.root, config, "path", 
                self.mock_context.state_mirror_engine, "topic", 
                self.mock_context.subscriber_router, self.mock_builder
            )
            
            # Initial state (default False)
            self.assertFalse(btn.variable.get())
            
            # Toggle
            btn._on_toggle()
            self.assertTrue(btn.variable.get())
            
            btn.destroy()

if __name__ == '__main__':
    unittest.main()
