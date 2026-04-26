# fader_dual/test_fader_dual.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiElements.Core.faders.fader_dual.Core.fader_dual import BuilderFaderDualCreator, CustomDualFaderFrame


class TestFaderDual(unittest.TestCase):
    def setUp(self):
        self.patchers = []
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = "#2b2b2b"

            MODULE = 'oaGuiElements.Core.faders.fader_dual.Core.fader_dual'
            self.patchers.append(patch(f'{MODULE}.tk.DoubleVar'))
            self.patchers.append(patch(f'{MODULE}.tk.Canvas'))
            self.patchers.append(patch(f'{MODULE}.tk.Frame'))

            for p in self.patchers:
                mock_cls = p.start()
                if hasattr(mock_cls, 'return_value'):
                    mock_cls.return_value.winfo_exists.return_value = True
                    mock_cls.return_value.cget.return_value = "#2b2b2b"

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
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        if hasattr(self.root, "destroy") and not isinstance(self.root, MagicMock):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
