# fader_dual/test_fader_dual.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.faders.fader_dual.fader_dual import CustomDualFaderFrame, BuilderFaderDualCreator

class TestFaderDual(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.config = {
            "label_active": "Test Dual Fader",
            "path": "test/dual_fader",
            "value_min": 0,
            "value_max": 100
        }
        self.mirror_engine = MagicMock()
        self.router = MagicMock()
        
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = "test/topic"
        self.context.builder_instance = MagicMock()

    def test_dual_fader_initialization(self):
        """Goal: Verify that CustomDualFaderFrame initializes correctly."""
        fader = CustomDualFaderFrame(
            master=self.root,
            config=self.config,
            path="test/dual_fader",
            state_mirror_engine=self.mirror_engine,
            base_mqtt_topic="test/topic",
            subscriber_router=self.router
        )
        self.assertEqual(fader.path, "test/dual_fader")
        self.assertEqual(fader.min_val, 0.0)

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderFaderDualCreator creates a dual fader frame."""
        fader = BuilderFaderDualCreator.make(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        self.assertIsInstance(fader, CustomDualFaderFrame)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
