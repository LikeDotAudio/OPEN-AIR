import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.metering.meter_needle.meter_needle import BuilderMeterNeedleCreator

class TestMeterNeedle(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.config = {
            "label_active": "Test Needle",
            "path": "test/needle",
            "meter_mode": "mono",
            "red_zone_start": 0.0,
            "peak_hold_ms": 1000
        }
        self.mirror_engine = MagicMock()
        self.mirror_engine.calculate_topic.return_value = "test/topic"
        
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/base"
        self.context.subscriber_router = MagicMock()
        self.context.builder_instance = MagicMock()

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderMeterNeedleCreator creates a needle meter."""
        # BUILD
        creator = BuilderMeterNeedleCreator()
        
        # OPERATE
        meter_frame = creator.make_meter_needle(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        
        # CHECK
        self.assertIsInstance(meter_frame, tk.Frame)
        # Check if the expected variables are attached to the frame (StateLinker adds them)
        self.assertTrue(hasattr(meter_frame, "vu_value_var"))
        self.assertIsInstance(meter_frame.vu_value_var, tk.DoubleVar)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
