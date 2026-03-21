import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.buttons.button_toggler.button_toggler import BuilderButtonTogglerCreator

class TestButtonToggler(unittest.TestCase):

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
            mock_var = MagicMock()
            self.patchers.append(patch('tkinter.IntVar', return_value=mock_var))
            for p in self.patchers:
                p.start()
        self.config = {'label': 'Test Toggler', 'path': 'test/toggler', 'options': {'A': {'label_active': 'A', 'val': 1}, 'B': {'label_active': 'B', 'val': 2}}, 'layout': {'width': 100, 'height': 50}}
        self.mirror_engine = MagicMock()
        self.router = MagicMock()
        self.builder = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = 'test/topic'
        self.context.builder_instance = self.builder

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderButtonTogglerCreator creates a toggler group.'
            creator = BuilderButtonTogglerCreator()
            widget = creator.make_button_toggler(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsNotNone(widget, 'Expected widget to be not None')
        except Exception as e:
            self.fail(f'Test builder creator make crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()