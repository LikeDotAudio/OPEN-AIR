import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.text.text_value_box.text_value_box import BuilderTextValueBoxCreator

class TestTextValueBox(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            mock_canvas = MagicMock()
            mock_canvas.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Canvas', return_value=mock_canvas))
            self.patchers.append(patch('tkinter.ttk.Style', return_value=MagicMock()))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test Box', 'path': 'test/box', 'value': '123', 'units': 'V'}
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/base'
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_make_text_value_box(self):
        try:
            'Goal: Verify that BuilderTextValueBoxCreator creates a value box widget.'
            creator = BuilderTextValueBoxCreator()
            box_widget = creator.make_text_value_box(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsNotNone(box_widget, 'Expected box_widget to be not None')
            self.mirror_engine.register_widget.assert_called()
        except Exception as e:
            self.fail(f'Test make text value box crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()