import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.text.text_label.text_label import BuilderTextLabelCreator

class TestTextLabel(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.config = {
            "label_active": "Test Label",
            "path": "test/label",
            "value": "Initial Value",
            "units": "Hz"
        }
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/base"
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_make_text_label(self):
        """Goal: Verify that BuilderTextLabelCreator creates a label widget (canvas)."""
        # BUILD
        creator = BuilderTextLabelCreator()
        
        # OPERATE
        label_widget = creator.make_text_label(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        
        # CHECK
        self.assertIsInstance(label_widget, tk.Canvas)
        self.mirror_engine.register_widget.assert_called()

    def test_static_make(self):
        """Goal: Verify the static make method."""
        # BUILD & OPERATE
        label_widget = BuilderTextLabelCreator.make(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        
        # CHECK
        self.assertIsInstance(label_widget, tk.Canvas)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
