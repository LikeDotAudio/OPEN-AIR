import unittest
import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.buttons.button_toggle.button_toggle import BuilderButtonToggleCreator

class TestButtonToggle(unittest.TestCase):
    def setUp(self):
        self.root = None
        self.patchers = []

        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = "#000000"

        # ⚡ PREDICTABLE STATE: Always patch BooleanVar so we can verify it
        self.mock_bool_var = MagicMock()
        self.mock_bool_var.get.return_value = False
        self.patchers.append(patch('tkinter.BooleanVar', return_value=self.mock_bool_var))
        
        # Patch Canvas if we're in headless
        if isinstance(self.root, MagicMock):
            mock_canvas = MagicMock()
            mock_canvas.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Canvas', return_value=mock_canvas))

        for p in self.patchers: p.start()

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
        try:
            creator = BuilderButtonToggleCreator()
            widget = creator.make_button_toggle(
                parent_widget=self.root,
                config_data=self.config,
                context=self.context
            )
            self.assertIsNotNone(widget, "BuilderButtonToggleCreator.make_button_toggle returned None")
        except Exception as e:
            self.fail(f"BuilderButtonToggleCreator.make_button_toggle crashed. Error: {str(e)}")

    def test_toggle_registration(self):
        """Goal: Verify that the toggle button registers itself with the mirror engine."""
        try:
            creator = BuilderButtonToggleCreator()
            # Ensure topic_widgets is initialized on the creator instance for this test.
            creator.topic_widgets = {} 
            widget = creator.make_button_toggle(
                parent_widget=self.root,
                config_data=self.config,
                context=self.context
            )
            self.assertIsNotNone(widget, "Widget creation failed during registration test")
            
            # Assert that mirror_engine.register_widget was called.
            try:
                self.mirror_engine.register_widget.assert_called()
            except AssertionError:
                self.fail("mirror_engine.register_widget was not called during toggle creation")

            # Assert that the correct state variable was stored in topic_widgets.
            self.assertIn(self.config["path"], creator.topic_widgets, f"Path '{self.config['path']}' not found in topic_widgets")
            self.assertEqual(creator.topic_widgets[self.config["path"]][0], self.mock_bool_var, "Stored BooleanVar does not match expected mock")
        except Exception as e:
            self.fail(f"Toggle registration test crashed. Error: {str(e)}")

if __name__ == "__main__":
    unittest.main()
