# meter_needle/test_meter_needle.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiElements.Core.metering.meter_needle.Core.meter_needle import BuilderMeterNeedleCreator


class TestMeterNeedle(unittest.TestCase):
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
            self.root.tk = MagicMock()

            # Patch variables
            self.patchers.append(patch("tkinter.DoubleVar"))
            self.patchers.append(patch("tkinter.StringVar"))
            self.patchers.append(patch("tkinter.IntVar"))

            # Patch Canvas and Frame in the UI factory
            UI_MODULE = 'oaGuiElements.Core.metering.meter_needle.ui.frame_factory'
            self.patchers.append(patch(f"{UI_MODULE}.tk.Canvas"))

            for p in self.patchers:
                mock_cls = p.start()
                mock_cls.return_value = MagicMock()
                mock_cls.return_value.winfo_exists.return_value = True
                mock_cls.return_value.tk = MagicMock()

            # Patch PIL
            self.patchers.append(patch("PIL.Image.open"))
            self.patchers.append(patch("PIL.ImageTk.PhotoImage"))
            for p in self.patchers[3:]: # Start from PIL patches
                p.start()

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
        self.assertIsNotNone(meter_frame)
        if self.HAS_DISPLAY:
            self.assertIsInstance(meter_frame, tk.Canvas)

        # Check if the expected variables are attached to the frame (StateLinker adds them)
        self.assertTrue(hasattr(meter_frame, "vu_value_var"))

    def test_tilted_meter_config_extraction(self):
        """Goal: Verify that tilt and crop commands are extracted from style_overrides and pointer."""
        from oaGuiElements.Core.metering.meter_needle.config.meter_config import MeterConfig
        test_config = {
            "cosmetics": {
                "style_overrides": {
                    "Meter_viewable_angle": 120,
                    "Meter_center_angle": 270,
                    "pivot_crop": 0.5
                },
                "pointer": {
                    "pivot_crop": 0.75
                }
            }
        }
        configuration = MeterConfig(test_config)
        self.assertEqual(configuration.meter_viewable_angle, 120.0)
        self.assertEqual(configuration.meter_center_angle, 270.0)
        # Should pull from style_overrides first
        self.assertEqual(configuration.pivot_crop, 0.5)

        test_config_2 = {
            "cosmetics": {
                "pointer": {
                    "pivot_crop": 0.75
                }
            }
        }
        cfg2 = MeterConfig(test_config_2)
        # Should fallback to pointer
        self.assertEqual(cfg2.pivot_crop, 0.75)

    def tearDown(self):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
