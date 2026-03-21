import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.metering.meter_needle.meter_needle import BuilderMeterNeedleCreator

class TestMeterNeedle(unittest.TestCase):

    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = '#2b2b2b'
            mock_canvas = MagicMock()
            mock_canvas.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Canvas', return_value=mock_canvas))
            mock_frame = MagicMock()
            mock_frame.winfo_exists.return_value = True
            self.patchers.append(patch('tkinter.Frame', return_value=mock_frame))
            mock_var = MagicMock()
            self.patchers.append(patch('tkinter.DoubleVar', return_value=mock_var))
            for p in self.patchers:
                p.start()
        self.config = {'label_active': 'Test Needle', 'path': 'test/needle', 'meter_mode': 'mono', 'red_zone_start': 0.0, 'peak_hold_ms': 1000}
        self.mirror_engine = MagicMock()
        self.mirror_engine.calculate_topic.return_value = 'test/topic'
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/base'
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderMeterNeedleCreator creates a needle meter.'
            creator = BuilderMeterNeedleCreator()
            meter_frame = creator.make_meter_needle(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsNotNone(meter_frame, 'Expected meter_frame to be not None')
            self.assertTrue(hasattr(meter_frame, 'vu_value_var'), "Expected hasattr(meter_frame, 'vu_value_var') to be True")
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