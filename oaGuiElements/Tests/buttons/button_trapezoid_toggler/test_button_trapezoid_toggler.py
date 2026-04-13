# button_trapezoid_toggler/test_button_trapezoid_toggler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.buttons.button_trapezoid_toggler.button_trapezoid_toggler import BuilderButtonTrapezoidTogglerCreator

class TestButtonTrapezoidToggler(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.config = {
            "label": "Test Trapezoid Toggler",
            "path": "test/trapezoid_toggler",
            "options": {
                "A": {"label_active": "A", "value": 1},
                "B": {"label_active": "B", "value": 2}
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

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderButtonTrapezoidTogglerCreator creates a group."""
        from oaGuiElements.Core.buttons.button_trapezoid.button_trapezoid import TrapezoidButton
        creator = BuilderButtonTrapezoidTogglerCreator()
        with patch.object(TrapezoidButton, 'winfo_width', return_value=80), \
             patch.object(TrapezoidButton, 'winfo_height', return_value=50):
            widget = creator.make_button_trapezoid_toggler(
                parent_widget=self.root,
                config_data=self.config,
                context=self.context
            )
            self.assertIsInstance(widget, tk.Canvas)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
