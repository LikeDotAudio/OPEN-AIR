# fader_horizontal/test_fader_horizontal.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock

from oaGuiElements.Core.faders.fader_horizontal.Core.fader_horizontal import (
    BuilderFaderHorizontalCreator,
    CustomHorizontalFaderFrame,
)


class TestFaderHorizontal(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()

        self.variable = tk.DoubleVar(master=self.root, value=50.0)
        self.config = {
            "label_active": "Test Horizontal Fader",
            "path": "test/horizontal_fader",
            "value_min": 0,
            "value_max": 100
        }
        self.mirror_engine = MagicMock()

        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/topic"

    def test_horizontal_fader_initialization(self):
        """Goal: Verify that CustomHorizontalFaderFrame initializes correctly."""
        fader = CustomHorizontalFaderFrame(
            master=self.root,
            variable=self.variable,
            config=self.config,
            path="test/horizontal_fader",
            state_mirror_engine=self.mirror_engine
        )
        self.assertEqual(fader.path, "test/horizontal_fader")
        self.assertEqual(fader.min_val, 0.0)

    def test_builder_creator_make(self):
        """Goal: Verify that BuilderFaderHorizontalCreator creates a horizontal fader frame."""
        fader = BuilderFaderHorizontalCreator.make(
            parent_widget=self.root,
            config_data=self.config,
            context=self.context
        )
        self.assertIsInstance(fader, CustomHorizontalFaderFrame)

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
