import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiElements.Core.utils.knob.knob import CustomKnobFrame

class TestKnobWidget(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.variable = tk.DoubleVar(master=self.root, value=0.5)
        # ⚡ FIX: Add required domain/min/max keys to avoid KeyError
        self.config = {
            "dynamics": {"path": "test/knob"},
            "cosmetics": {"label": "Test Knob"},
            "domain": {"primary": {"min": 0, "max": 100}},
            "geometry": {"width": 50, "height": 50}
        }
        self.state = {
            "dims": {"w": 50, "h": 50},
            "secondary_current": "#444444"
        }
        self.mirror_engine = MagicMock()
        
        # We need to mock extract_knob_config or provide EXACT expected keys
        # CustomKnobFrame calls extract_knob_config in some internal methods if not careful,
        # but here we pass the result of extraction or enough data.
        
        extracted_config = {
            "min": 0, "max": 100, "width": 50, "height": 50, "bg_color": "#2b2b2b",
            "secondary_color": "#444444", "indicator_color": "#33A1FD", "accent_color": "#33A1FD",
            "reff_point": 50, "value_default": 0, "infinity": False, "fine_pitch": False,
            "text_pos": "top", "show_label": True, "text_inside": False, "knob_style": "standard",
            "shape": "circle", "pointer_style": "line", "tick_style": "simple", "gradient_level": 0,
            "outline_thickness": 0, "outline_color": "#444444", "fill_color": "", "teeth": 8,
            "no_center": False, "show_ticks": False, "tick_length": 10, "arc_width": 5,
            "pointer_length": None, "pointer_offset": 0, "fg_color": "#dcdcdc"
        }
        
        with patch("oaGuiElements.Core.utils.knob.knob.extract_knob_config", return_value=extracted_config):
            self.knob = CustomKnobFrame(
                parent=self.root,
                variable=self.variable,
                config=extracted_config,
                state=self.state,
                path="test/knob",
                state_mirror_engine=self.mirror_engine,
                label_text="Test Knob"
            )

    def test_initialization(self):
        """Goal: Verify that the Knob frame initializes its internal state."""
        self.assertEqual(self.knob.path, "test/knob")

    def test_broadcast_notifies_engine(self):
        """Goal: Verify that broadcast_change triggers the mirror engine."""
        self.knob._broadcast_cb()
        self.mirror_engine.broadcast_gui_change_to_mqtt.assert_called_with("test/knob")

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

if __name__ == "__main__":
    unittest.main()
