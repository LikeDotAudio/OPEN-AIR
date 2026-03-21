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
        self.config = {'label_active': 'Test Label', 'path': 'test/label', 'value': 'Initial Value', 'units': 'Hz'}
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/base'
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_make_text_label(self):
        try:
            'Goal: Verify that BuilderTextLabelCreator creates a label widget (canvas).'
            creator = BuilderTextLabelCreator()
            label_widget = creator.make_text_label(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsInstance(label_widget, tk.Canvas, f'Expected instance of tk.Canvas, got {type(label_widget)}')
            self.mirror_engine.register_widget.assert_called()
        except Exception as e:
            self.fail(f'Test make text label crashed. Error: {str(e)}')

    def test_static_make(self):
        try:
            'Goal: Verify the static make method.'
            label_widget = BuilderTextLabelCreator.make(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsInstance(label_widget, tk.Canvas, f'Expected instance of tk.Canvas, got {type(label_widget)}')
        except Exception as e:
            self.fail(f'Test static make crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()