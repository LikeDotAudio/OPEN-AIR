import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import os
import json

from oaGuiElements.Core.Knobs.knob_rotary_selector.knob_rotary_selector import RotarySelectorSwitch, BuilderKnobRotarySelectorCreator

# Helper to load sample config
def load_sample_config():
    # Correctly locate the sample.json relative to this test file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sample_path = os.path.join(dir_path, '../../../Core/Knobs/knob_rotary_selector/sample.json')
    with open(sample_path, 'r') as f:
        return json.load(f)

class TestRotarySelector(unittest.TestCase):

    def setUp(self):
        # Create a root window for the tests
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window

        self.config_data = load_sample_config()
        
        # Correctly handle default value if it's a string
        if isinstance(self.config_data.get("value_default"), str):
            try:
                default_val_index = self.config_data['positions'].index(self.config_data['value_default'])
                self.variable = tk.DoubleVar(value=default_val_index)
            except (ValueError, KeyError):
                self.variable = tk.DoubleVar(value=0) # Fallback
        else:
            self.variable = tk.DoubleVar(value=self.config_data.get("value_default", 0))

        self.positions = self.config_data.get("positions", ["A", "B", "C"])

        # Mock dependencies
        self.state_mirror_engine = MagicMock()

        # Patch themes to avoid deep style dependencies
        self.theme_patch = patch('oaStyle.Core.style.THEMES', {'dark': {'knob': {}}})
        self.mock_themes = self.theme_patch.start()

        # Use a real config extracted from sample, but mock the state for simplicity
        from oaGuiElements.Core.Knobs.knob.Core.knob_config import extract_knob_config
        self.knob_config = extract_knob_config(self.config_data)
        self.knob_state = MagicMock()

        self.selector = RotarySelectorSwitch(
            parent=self.root,
            variable=self.variable,
            positions=self.positions,
            continuous=self.config_data.get("continuous", False),
            path="test/selector",
            state_mirror_engine=self.state_mirror_engine,
            config=self.knob_config,
            state=self.knob_state,
            label_text="Test Selector",
            width=self.config_data.get("width", 150),
            height=self.config_data.get("height", 150)
        )

    def test_01_initialization(self):
        """Verify the selector initializes with the correct number of positions."""
        self.assertIsInstance(self.selector, RotarySelectorSwitch)
        self.assertEqual(self.selector.num_positions, len(self.positions))
        self.assertEqual(self.selector.path, "test/selector")
        self.assertEqual(self.selector.label_text, "Test Selector")

    def test_02_draw_visuals_calls_internal_methods(self):
        """Ensure _draw_visuals triggers the main drawing pipeline."""
        with patch.object(self.selector, '_draw_selector') as mock_draw_selector:
            self.selector._draw_visuals()
            mock_draw_selector.assert_called_once()

    def test_03_value_change_updates_selection_text(self):
        """Check if changing the variable updates the displayed text."""
        # Mock the drawing method to inspect its arguments
        with patch.object(self.selector, '_draw_selector') as mock_draw_selector:
            # Change value to the index of the second position
            self.variable.set(1)
            self.selector._draw_visuals()
            
            # The options dict passed to _draw_selector should contain the correct text
            call_args, call_kwargs = mock_draw_selector.call_args
            options_arg = call_kwargs.get('options') or (call_args[6] if len(call_args) > 6 else {})
            self.assertEqual(options_arg.get('selection_text'), self.positions[1])

            # Change value to the index of the third position
            self.variable.set(2)
            self.selector._draw_visuals()
            call_args, call_kwargs = mock_draw_selector.call_args
            options_arg = call_kwargs.get('options') or (call_args[6] if len(call_args) > 6 else {})
            self.assertEqual(options_arg.get('selection_text'), self.positions[2])

    def test_04_builder_creation(self):
        """Verify the Builder can create a RotarySelectorSwitch instance."""
        mock_context = MagicMock()
        mock_context.state_mirror_engine = MagicMock()
        mock_context.subscriber_router = MagicMock()
        mock_context.base_mqtt_topic_from_path = "OPEN-AIR"
        mock_context.builder_instance = MagicMock()

        # Patch TransparencyManager to avoid GUI dependencies
        with patch('oaGuiManager.Core.transparency.transparency.TransparencyManager.apply_transparency'):
            widget = BuilderKnobRotarySelectorCreator.make(
                self.root,
                self.config_data,
                context=mock_context
            )

        self.assertIsInstance(widget, RotarySelectorSwitch)
        self.assertEqual(widget.num_positions, len(self.config_data["positions"]))
        self.assertEqual(widget.label_text, self.config_data["label_active"])
        
        # Check that the state mirror engine was called for registration
        mock_context.state_mirror_engine.register_widget.assert_called_once()


    def tearDown(self):
        # Stop the patcher
        self.theme_patch.stop()
        self.root.destroy()

if __name__ == '__main__':
    # This allows running the test script directly
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
