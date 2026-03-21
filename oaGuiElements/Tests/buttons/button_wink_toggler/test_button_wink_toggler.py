import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.buttons.button_wink_toggler.button_wink_toggler import BuilderButtonWinkTogglerCreator

class TestButtonWinkToggler(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.BooleanVar', return_value=MagicMock()))
            mock_canvas = MagicMock()
            mock_canvas.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Canvas', return_value=mock_canvas))
            self.patchers.append(patch('PIL.ImageTk.PhotoImage', return_value=MagicMock()))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test Wink Toggler', 'path': 'test/wink_toggler', 'options': {'A': {'label_active': 'A', 'val': 1}, 'B': {'label_active': 'B', 'val': 2}}}
        self.mirror_engine = MagicMock()
        self.router = MagicMock()
        self.builder = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = 'test/topic'
        self.context.builder_instance = self.builder
        self.context.app_instance = MagicMock()

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderButtonWinkTogglerCreator creates a group.'
            creator = BuilderButtonWinkTogglerCreator()
            widget = creator.make_button_wink_toggler(parent_widget=self.root, config_data=self.config, context=self.context)
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