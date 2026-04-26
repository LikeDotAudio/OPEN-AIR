# button_trapezoid/test_button_trapezoid.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiElements.Core.buttons.button_trapezoid.Core.button_trapezoid import TrapezoidButton


class TestButtonTrapezoid(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()

        # Fixed DoubleVar master
        self.variable = tk.DoubleVar(master=self.root, value=0.0)
        self.config = {
            "label": "Test Trapezoid",
            "path": "test/trapezoid",
            "width": 80,
            "height": 50,
            "latching": True
        }
        self.mirror_engine = MagicMock()
        self.router = MagicMock()

        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.subscriber_router = self.router
        self.context.base_mqtt_topic_from_path = "test/topic"

    def test_trapezoid_button_initialization(self):
        """Goal: Verify that TrapezoidButton initializes correctly."""
        with patch.object(TrapezoidButton, 'winfo_width', return_value=80), \
             patch.object(TrapezoidButton, 'winfo_height', return_value=50):
            button = TrapezoidButton(
                parent=self.root,
                variable=self.variable,
                config=self.config,
                label="Test Trapezoid",
                path="test/trapezoid",
                state_mirror_engine=self.mirror_engine,
                base_mqtt_topic_from_path="test/topic",
                subscriber_router=self.router
            )
            self.assertEqual(button.path, "test/trapezoid")
            self.assertEqual(button.label, "Test Trapezoid")

    def test_trapezoid_registration(self):
        """Goal: Verify that TrapezoidButton registers with state mirror engine."""
        with patch.object(TrapezoidButton, 'winfo_width', return_value=80), \
             patch.object(TrapezoidButton, 'winfo_height', return_value=50):
            TrapezoidButton(
                parent=self.root,
                variable=self.variable,
                config=self.config,
                label="Test Trapezoid",
                path="test/trapezoid",
                state_mirror_engine=self.mirror_engine,
                base_mqtt_topic_from_path="test/topic",
                subscriber_router=self.router
            )
            self.mirror_engine.register_widget.assert_called()

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
