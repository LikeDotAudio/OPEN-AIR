# fader_linear_travelling_potentiometer/test_fader_linear_travelling_potentiometer.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.faders.fader_linear_travelling_potentiometer.Core.fader_linear_travelling_potentiometer import CustomLTPFrame, BuilderFaderLinearTravellingPotentiometerCreator

class TestFaderLinearTravellingPotentiometer(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.config = {
            "label_active": "Test LTP",
            "path": "test/ltp",
            "fader_config": {
                "value_min": 0,
                "value_max": 100,
                "value_default": 50.0
            },
            "knob_config": {
                "rotation_min": -100,
                "rotation_max": 100,
                "rotation_default": 0.0
            }
        }
        self.mirror_engine = MagicMock()
        self.mirror_engine.calculate_topic.return_value = "test/topic"
        
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/base"
        self.context.subscriber_router = MagicMock()

    def test_ltp_initialization(self):
        """Goal: Verify that CustomLTPFrame initializes correctly."""
        # BUILD
        ltp = CustomLTPFrame(
            master=self.root,
            config=self.config,
            path="test/ltp",
            state_mirror_engine=self.mirror_engine,
            subscriber_router=self.context.subscriber_router,
            base_mqtt_topic="test/base"
        )
        
        # OPERATE & CHECK
        self.assertEqual(ltp.path, "test/ltp")
        self.assertEqual(ltp.min_val, 0.0)
        self.assertEqual(ltp.max_val, 100.0)
        self.assertEqual(ltp.linear_var.get(), 50.0)
        self.assertEqual(ltp.rotation_var.get(), 0.0)

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderFaderLinearTravellingPotentiometerCreator creates an LTP frame."""
        # BUILD & OPERATE
        ltp = BuilderFaderLinearTravellingPotentiometerCreator.make(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        
        # CHECK
        self.assertIsInstance(ltp, CustomLTPFrame)
        self.mirror_engine.register_widget.assert_called()

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
