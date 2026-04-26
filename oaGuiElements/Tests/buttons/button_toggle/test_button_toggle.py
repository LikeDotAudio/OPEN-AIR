# button_toggle/test_button_toggle.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiElements.Core.buttons.button_toggle.Core.button_toggle import BuilderButtonToggleCreator


class TestButtonToggle(unittest.TestCase):
    def setUp(self):
        self.root = None
        self.mock_bool_var = None # Initialize to None
        self.patchers = [] # To keep track of active patches.

        try:
            # Attempt to create a real Tk root.
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            # Tkinter is not available, create a mock root and patch Tkinter components.
            self.root = MagicMock()
            # Mock methods expected on a Tkinter widget when used as a parent.
            self.root.winfo_width.return_value = 200
            self.root.winfo_height.return_value = 100
            self.root.cget.return_value = "#000000" # Default background color for mock root.
            self.root.configure.return_value = None
            self.root.destroy.return_value = None
            self.root.winfo_exists.return_value = True
            self.root.bind.return_value = None
            self.root.children = {} # Mock children attribute if needed.

            # Mock instance for tk.Canvas.
            mock_canvas_instance = MagicMock()
            mock_canvas_instance.winfo_width.return_value = 100 # Default width for the canvas.
            mock_canvas_instance.winfo_height.return_value = 50 # Default height for the canvas.
            mock_canvas_instance.cget.side_effect = lambda key: {
                "bg": "#1a1a1a", "width": 100, "height": 50, "bd": 0, "highlightthickness": 0, "relief": "flat"
            }.get(key, None) # Mock cget to return common canvas properties.
            mock_canvas_instance.configure.return_value = None
            mock_canvas_instance.winfo_exists.return_value = True
            mock_canvas_instance.bind.return_value = None
            mock_canvas_instance._last_redraw_size = (0,0) # For redraw_labels logic.

            # Mock instance for tk.BooleanVar.
            self.mock_bool_var = MagicMock() # Assign mock_bool_var here
            self.mock_bool_var.get.return_value = False # Default state for BooleanVar.
            self.mock_bool_var.trace_add.return_value = None

            # Patch tkinter.Canvas and tkinter.BooleanVar.
            canvas_patcher = patch('tkinter.Canvas', return_value=mock_canvas_instance)
            self.patchers.append(canvas_patcher)
            canvas_patcher.start()

            bool_var_patcher = patch('tkinter.BooleanVar', return_value=self.mock_bool_var)
            self.patchers.append(bool_var_patcher)
            bool_var_patcher.start()

            # Ensure tk.TclError is available for the try-except block to catch.
            tk.TclError = tk.TclError

        # Common mocks setup, independent of Tkinter availability.
        self.config = {
            "label": "Test Toggle",
            "path": "test/toggle",
            "active_color": "#FF9900",
            "bg_color": "#1a1a1a",
            "options": {
                "ON": {"selected": True},
                "OFF": {"selected": False}
            }
        }
        self.mirror_engine = MagicMock()
        # Mock register_widget to return a topic string, simulating a successful registration.
        self.mirror_engine.register_widget.return_value = "test/topic/button_toggle"
        self.router = MagicMock()
        self.builder = MagicMock()
        # Mock the _apply_transparency method, which is called within make_button_toggle.
        self.builder._apply_transparency = MagicMock()

        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = "test/topic"
        self.context.builder_instance = self.builder
        self.context.app_instance = MagicMock()

    def tearDown(self):
        # Stop all active patches.
        for patcher in self.patchers:
            patcher.stop()

        # Destroy the Tkinter root window if it's a real Tk instance.
        if self.root and isinstance(self.root, tk.Tk):
            self.root.destroy()
        # If it's a mock, call its destroy method if it exists.
        elif hasattr(self.root, 'destroy'):
            self.root.destroy()

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderButtonToggleCreator creates a toggle button widget."""
        creator = BuilderButtonToggleCreator()
        widget = creator.make_button_toggle(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        # Assert that a widget was created (not None).
        self.assertIsNotNone(widget)
        # Additional assertions could verify widget type or specific method calls.

    def test_toggle_registration(self):
        """Goal: Verify that the toggle button registers itself with the mirror engine."""
        creator = BuilderButtonToggleCreator()
        widget = creator.make_button_toggle(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        self.assertIsNotNone(widget)
        # Assert that mirror_engine.register_widget was called.
        self.mirror_engine.register_widget.assert_called()

if __name__ == "__main__":
    unittest.main()

    unittest.main()
