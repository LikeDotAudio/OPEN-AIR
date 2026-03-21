import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.metering.meter_bar.meter_bar import BuilderMeterBarCreator
from oaGuiElements.Core.metering.meter_bar.smart_meter import SmartMeter

class TestMeterBar(unittest.TestCase):

    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        self.config = {'label_active': 'Test Meter', 'path': 'test/meter', 'meter_config': {'min_val': -60.0, 'max_val': 12.0}}
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = 'test/base'
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_smart_meter_initialization(self):
        try:
            'Goal: Verify that SmartMeter initializes correctly.'
            meter = SmartMeter(parent=self.root, raw_config=self.config, state_mirror_engine=self.mirror_engine, subscriber_router=self.context.subscriber_router, base_topic='test/base')
            self.assertIsInstance(meter.value_var, tk.DoubleVar, f'Expected instance of tk.DoubleVar, got {type(meter.value_var)}')
            self.assertTrue(hasattr(meter, 'canvas'), "Expected hasattr(meter, 'canvas') to be True")
        except Exception as e:
            self.fail(f'Test smart meter initialization crashed. Error: {str(e)}')

    def test_builder_creator_make(self):
        try:
            'Goal: Verify that BuilderMeterBarCreator creates a SmartMeter.'
            meter = BuilderMeterBarCreator.make(parent_widget=self.root, config_data=self.config, context=self.context)
            self.assertIsInstance(meter, SmartMeter, f'Expected instance of SmartMeter, got {type(meter)}')
            self.mirror_engine.register_widget.assert_called()
        except Exception as e:
            self.fail(f'Test builder creator make crashed. Error: {str(e)}')

    def tearDown(self):
        if hasattr(self.root, 'destroy'):
            self.root.destroy()
if __name__ == '__main__':
    unittest.main()