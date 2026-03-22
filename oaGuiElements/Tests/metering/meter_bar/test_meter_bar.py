# meter_bar/test_meter_bar.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.metering.meter_bar.meter_bar import BuilderMeterBarCreator
from oaGuiElements.Core.metering.meter_bar.smart_meter import SmartMeter

class TestMeterBar(unittest.TestCase):
    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
            self.HAS_DISPLAY = True
        except:
            self.HAS_DISPLAY = False
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = "#2b2b2b"
            self.root.tk = MagicMock()
            
            # Patch classes in the TARGET module to return mocks
            METER_MODULE = 'oaGuiElements.Core.metering.meter_bar.smart_meter'
            self.patchers.append(patch(f'{METER_MODULE}.tk.Canvas'))
            self.patchers.append(patch(f'{METER_MODULE}.tk.DoubleVar', return_value=MagicMock()))
            
            for p in self.patchers:
                mock_cls = p.start()
                if hasattr(mock_cls, 'return_value'):
                    mock_cls.return_value.winfo_exists.return_value = True
                    mock_cls.return_value.tk = MagicMock()
        
        self.config = {
            "label_active": "Test Meter",
            "path": "test/meter",
            "meter_config": {
                "min_val": -60.0,
                "max_val": 12.0
            }
        }
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/base"
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_smart_meter_initialization(self):
        """Goal: Verify that SmartMeter initializes correctly."""
        # BUILD
        meter = SmartMeter(
            parent=self.root,
            raw_config=self.config,
            state_mirror_engine=self.mirror_engine,
            subscriber_router=self.context.subscriber_router,
            base_topic="test/base"
        )
        
        # OPERATE & CHECK
        if self.HAS_DISPLAY:
            self.assertIsInstance(meter.value_var, tk.DoubleVar)
        else:
            self.assertIsNotNone(meter.value_var)
            
        # Just checking basic initialization success here.
        self.assertTrue(hasattr(meter, "canvas"))

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderMeterBarCreator creates a SmartMeter."""
        # BUILD & OPERATE
        meter = BuilderMeterBarCreator.make(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        
        # CHECK
        self.assertIsNotNone(meter)
        if self.HAS_DISPLAY:
            self.assertIsInstance(meter, tk.Canvas)
        self.mirror_engine.register_widget.assert_called()

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
