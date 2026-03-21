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
        self.config = {'label': 'Test Trapezoid Toggler', 'path': 'test/trapezoid_toggler', 'options': {'A': {'label_active': 'A', 'val': 1}, 'B': {'label_active': 'B', 'val': 2}}}
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
            'Goal: Verify that BuilderButtonTrapezoidTogglerCreator creates a group.'
            creator = BuilderButtonTrapezoidTogglerCreator()
            widget = creator.make_button_trapezoid_toggler(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsInstance(widget, tk.Canvas, f'Expected instance of tk.Canvas, got {type(widget)}')
        except Exception as e:
            self.fail(f'Test builder creator make crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()