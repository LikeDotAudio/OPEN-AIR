# fader/test_fader.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock

from oaGuiElements.Core.faders.fader.Core.fader import BuilderFaderCreator, CustomFaderFrame


class TestFader(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()

        self.variable = tk.DoubleVar(master=self.root, value=50.0)
        self.config = {
            "label_active": "Test Fader",
            "path": "test/fader",
            "value_min": 0,
            "value_max": 100
        }
        self.mirror_engine = MagicMock()

        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/topic"

    def test_fader_initialization(self):
        """Goal: Verify that CustomFaderFrame initializes correctly."""
        fader = CustomFaderFrame(
            master=self.root,
            variable=self.variable,
            config=self.config,
            path="test/fader",
            state_mirror_engine=self.mirror_engine,
            sync_callback=None
        )
        self.assertEqual(fader.path, "test/fader")
        self.assertEqual(fader.min_val, 0.0)
        self.assertEqual(fader.max_val, 100.0)

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderFaderCreator creates a fader frame."""
        fader = BuilderFaderCreator.make(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        self.assertIsInstance(fader, CustomFaderFrame)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
