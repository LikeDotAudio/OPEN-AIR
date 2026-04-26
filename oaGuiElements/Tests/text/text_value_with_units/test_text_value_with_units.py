# text_value_with_units/test_text_value_with_units.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiElements.Core.text.text_value_box.Core.text_value_box import BuilderTextValueBoxCreator


class TestTextValueBox(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()

        self.config = {
            "label_active": "Test Box",
            "path": "test/box",
            "value": "123",
            "units": "V"
        }
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/base"
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_make_text_value_box(self):
        """Goal: Verify that BuilderTextValueBoxCreator creates a value box widget."""
        # BUILD
        creator = BuilderTextValueBoxCreator()

        # OPERATE
        with patch('tkinter.ttk.Style'):
            box_widget = creator.make_text_value_box(
                parent_widget=self.root,
                config_data=self.config,
                context=self.context
            )

        # CHECK
        self.assertIsInstance(box_widget, tk.Canvas)
        self.mirror_engine.register_widget.assert_called()

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
