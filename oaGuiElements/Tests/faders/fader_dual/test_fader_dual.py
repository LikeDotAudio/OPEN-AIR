import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.faders.fader_dual.fader_dual import CustomDualFaderFrame, BuilderFaderDualCreator

class TestFaderDual(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.DoubleVar', return_value=MagicMock()))
            mock_canvas = MagicMock()
            mock_canvas.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Canvas', return_value=mock_canvas))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test Dual Fader', 'path': 'test/dual_fader', 'value_min': 0, 'value_max': 100}
        self.mirror_engine = MagicMock()
        self.router = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = 'test/topic'
        self.context.builder_instance = MagicMock()

    def test_dual_fader_initialization(self):
        try:
            'Goal: Verify that CustomDualFaderFrame initializes correctly.'
            fader = CustomDualFaderFrame(master=self.root, config=self.config, path='test/dual_fader', state_mirror_engine=self.mirror_engine, base_mqtt_topic='test/topic', subscriber_router=self.router)
            self.assertEqual(fader.path, 'test/dual_fader', f"Expected 'test/dual_fader', got '{fader.path}'")
            self.assertEqual(fader.min_val, 0.0, f"Expected 0.0, got '{fader.min_val}'")
        except Exception as e:
            self.fail(f'Test dual fader initialization crashed. Error: {str(e)}')

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderFaderDualCreator creates a dual fader frame.'
            fader = BuilderFaderDualCreator.make(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsNotNone(fader, 'Expected fader to be not None')
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