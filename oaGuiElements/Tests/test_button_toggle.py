import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.buttons.button_toggle.button_toggle import BuilderButtonToggleCreator

class TestButtonToggle(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
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
        self.router = MagicMock()
        self.builder = MagicMock()
        
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = "test/topic"
        self.context.builder_instance = self.builder
        self.context.app_instance = MagicMock()

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderButtonToggleCreator creates a toggle button widget."""
        creator = BuilderButtonToggleCreator()
        widget = creator.make_button_toggle(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        self.assertIsNotNone(widget)

    def test_toggle_registration(self):
        """Goal: Verify that the toggle button registers itself with the mirror engine."""
        creator = BuilderButtonToggleCreator()
        creator.topic_widgets = {}
        creator.make_button_toggle(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        self.mirror_engine.register_widget.assert_called()

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
