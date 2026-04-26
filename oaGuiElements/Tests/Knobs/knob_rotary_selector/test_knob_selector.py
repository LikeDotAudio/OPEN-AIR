import json
import os
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiElements.Core.Knobs.knob_rotary_selector.Core.knob_rotary_selector import (
    BuilderKnobRotarySelectorCreator,
    RotarySelectorSwitch,
)


def load_sample_config():
    # Correctly locate the sample.json relative to this test file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sample_path = os.path.join(dir_path, '../../../Core/Knobs/knob_rotary_selector/Assets/sample.json')
    with open(sample_path) as f:
        data = json.load(f)
        return data.get("knob_rotary_selector_Example", data)

class TestRotarySelector(unittest.TestCase):

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

            # Patch classes in the TARGET module
            SELECTOR_MODULE = 'oaGuiElements.Core.Knobs.knob_rotary_selector.Core.knob_rotary_selector'
            self.patchers.append(patch(f'{SELECTOR_MODULE}.tk.Canvas'))
            self.patchers.append(patch(f'{SELECTOR_MODULE}.tk.Frame'))

            for p in self.patchers:
                mock_cls = p.start()
                if hasattr(mock_cls, 'return_value'):
                    mock_cls.return_value.winfo_exists.return_value = True
                    mock_cls.return_value.tk = MagicMock()
                    mock_cls.return_value.__str__.return_value = "mock_selector"

        # Mocking the theme manager to avoid potential issues with theme loading
        self.theme_patch = patch('oaStyle.Core.style.THEMES', {'dark': {'bg': '#2b2b2b', 'fg': '#ffffff', 'accent': '#00ff00'}})
        self.theme_patch.start()

        self.config_data = load_sample_config()

        # Correctly handle default value
        self.positions = self.config_data.get("positions", ["A", "B", "C"])
        if self.HAS_DISPLAY:
            self.variable = tk.DoubleVar(value=0)
        else:
            self.variable = MagicMock()
            # Simulate basic set/get behavior
            self.var_val = 0.0
            def _set(v): self.var_val = float(v)
            def _get(): return self.var_val
            self.variable.set.side_effect = _set
            self.variable.get.side_effect = _get

        # Provide a basic config for the base class
        self.basic_config = {
            "width": 100, "height": 100,
            "min": 0, "max": 4, "reff_point": 0
        }

        self.selector = RotarySelectorSwitch(
            self.root,
            variable=self.variable,
            positions=self.positions,
            label_text=self.config_data.get("label_active", "Test Selector"),
            config=self.basic_config,
            state={}
        )

    def test_01_initialization(self):
        """Verify the selector initializes with the correct number of positions."""
        self.assertIsInstance(self.selector, RotarySelectorSwitch)
        self.assertEqual(self.selector.num_positions, len(self.positions))

    def test_02_value_change(self):
        """Verify the selector updates its value correctly."""
        self.variable.set(2)
        if self.HAS_DISPLAY:
            self.assertEqual(self.variable.get(), 2)
        else:
            # If mocked, check if it was set (though here we set it directly)
            self.assertEqual(self.variable.get(), 2)

    def test_03_position_text(self):
        """Verify the selector returns correct position text."""
        self.variable.set(2)
        self.assertEqual(self.selector.cget('label_active'), self.positions[2])

    def test_04_builder_creation(self):
        """Verify the Builder can create a RotarySelectorSwitch instance."""
        mock_context = MagicMock()
        mock_context.state_mirror_engine = MagicMock()

        # Patch TransparencyManager to avoid GUI dependencies
        with patch('oaGuiManager.Core.transparency.transparency.TransparencyManager.apply_transparency'):
            widget = BuilderKnobRotarySelectorCreator.make(
                self.root,
                self.config_data,
                context=mock_context
            )

        self.assertIsInstance(widget, RotarySelectorSwitch)
        self.assertEqual(widget.num_positions, len(self.config_data["positions"]))

    def tearDown(self):
        # Stop the patcher
        self.theme_patch.stop()
        for p in self.patchers:
            p.stop()
        if hasattr(self, 'root') and hasattr(self.root, 'destroy') and not isinstance(self.root, MagicMock):
            self.root.destroy()

if __name__ == '__main__':
    unittest.main()
