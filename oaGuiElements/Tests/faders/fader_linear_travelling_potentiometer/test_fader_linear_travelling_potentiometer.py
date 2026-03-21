import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.faders.fader_linear_travelling_potentiometer.fader_linear_travelling_potentiometer import CustomLTPFrame, BuilderFaderLinearTravellingPotentiometerCreator

class TestFaderLinearTravellingPotentiometer(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = '#2b2b2b'

            def make_mock_var(*args, **kwargs):
                value = kwargs.get('value', 0.0)
                m = MagicMock()
                m.get.return_value = value
                return m
            self.patchers.append(patch('tkinter.DoubleVar', side_effect=make_mock_var))
            self.patchers.append(patch('tkinter.StringVar', side_effect=make_mock_var))
            self.patchers.append(patch('tkinter.Canvas', return_value=MagicMock()))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test LTP', 'path': 'test/ltp', 'fader_config': {'value_min': 0, 'value_max': 100, 'value_default': 50.0}, 'knob_config': {'rotation_min': -100, 'rotation_max': 100, 'rotation_default': 0.0}}
        self.mirror_engine = MagicMock()
        self.mirror_engine.calculate_topic.return_value = 'test/topic'
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/base'
        self.context.subscriber_router = MagicMock()

    def test_ltp_initialization(self):
        try:
            'Goal: Verify that CustomLTPFrame initializes correctly.'
            ltp = CustomLTPFrame(master=self.root, config=self.config, path='test/ltp', state_mirror_engine=self.mirror_engine, subscriber_router=self.context.subscriber_router, base_mqtt_topic='test/base')
            self.assertEqual(ltp.path, 'test/ltp', f"Expected 'test/ltp', got '{ltp.path}'")
            self.assertEqual(ltp.min_val, 0.0, f"Expected 0.0, got '{ltp.min_val}'")
            self.assertEqual(ltp.max_val, 100.0, f"Expected 100.0, got '{ltp.max_val}'")
            self.assertEqual(ltp.linear_var.get(), 50.0, f"Expected 50.0, got '{ltp.linear_var.get()}'")
            self.assertEqual(ltp.rotation_var.get(), 0.0, f"Expected 0.0, got '{ltp.rotation_var.get()}'")
        except Exception as e:
            self.fail(f'Test ltp initialization crashed. Error: {str(e)}')

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderFaderLinearTravellingPotentiometerCreator creates an LTP frame.'
            ltp = BuilderFaderLinearTravellingPotentiometerCreator.make(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsInstance(ltp, CustomLTPFrame, f'Expected instance of CustomLTPFrame, got {type(ltp)}')
            self.mirror_engine.register_widget.assert_called()
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