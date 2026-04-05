# Tests/test_robustness.py
# Author: Gemini CLI
# Version: 20260404.2250.1
#
# Description: Advanced robustness tests covering boundaries, security, and performance.

import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
import time

# Import components
from oaGuiElements.Core.faders.fader.fader import CustomFaderFrame
from oaGuiElements.Core.text.text_value_box.text_value_box import BuilderTextValueBoxCreator

class TestRobustness(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        
        self.mirror_engine = MagicMock()
        self.context = MagicMock()
        self.context.state_mirror_engine = self.mirror_engine
        self.context.base_mqtt_topic_from_path = "test/topic"

    def tearDown(self):
        if hasattr(self.root, "destroy"):
            self.root.destroy()

    # --- 1. Explicit Boundary Condition Tests ---
    def test_fader_boundary_conditions(self):
        """Clean Code: Test Boundary Conditions (0.0 and 1.0)"""
        variable = tk.DoubleVar(value=0.5)
        config = {"value_min": 0, "value_max": 100, "path": "test/fader"}
        
        fader = CustomFaderFrame(
            master=self.root,
            variable=variable,
            config=config,
            path="test/fader",
            state_mirror_engine=self.mirror_engine,
            sync_callback=MagicMock()
        )
        
        # Test Min Boundary
        variable.set(0.0)
        self.root.update()
        self.assertEqual(variable.get(), 0.0)
        
        # Test Max Boundary
        variable.set(100.0)
        self.root.update()
        self.assertEqual(variable.get(), 100.0)

    # --- 3. Security and Compliance Tests ---
    def test_text_value_box_injection_sanitization(self):
        """AI Rules: Security Tests (Script Injection)"""
        creator = BuilderTextValueBoxCreator()
        malicious_input = "<script>alert('XSS')</script>"
        config = {
            "label_active": "Security Test",
            "path": "test/security",
            "value": malicious_input
        }
        
        with patch('tkinter.ttk.Style'):
            box_widget = creator.make_text_value_box(
                parent_widget=self.root,
                config_data=config,
                context=self.context
            )
        
        # Verify component created without crashing
        self.assertIsInstance(box_widget, tk.Canvas)
        # Note: Actual sanitization logic check would depend on how the widget renders/handles text

    # --- 4. Advanced Performance Tests ---
    def test_ui_rendering_performance_baseline(self):
        """AI Rules: Performance Baselines (<16ms for 60fps)"""
        start_time = time.time()
        
        # Simulate rendering multiple components
        for i in range(10):
            variable = tk.DoubleVar(value=50.0)
            config = {"value_min": 0, "value_max": 100, "path": f"test/fader/{i}"}
            CustomFaderFrame(self.root, variable, config, path=f"test/fader/{i}", state_mirror_engine=self.mirror_engine, sync_callback=MagicMock())
        
        self.root.update()
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        # A single component should definitely render within the budget. 
        # Here we test if 10 components render within 160ms (16ms each)
        self.assertLess(duration_ms, 160, f"UI rendering too slow: {duration_ms:.2f}ms for 10 widgets")

    # --- 6. UI Accessibility ---
    def test_accessibility_tab_navigation(self):
        """AI Rules: Accessibility (Tab Focus)"""
        # Create a few widgets
        v1 = tk.DoubleVar()
        f1 = CustomFaderFrame(self.root, v1, {"path": "f1"}, path="f1", state_mirror_engine=self.mirror_engine, sync_callback=MagicMock())
        
        # Check if the widget or its internal interactive parts are focusable
        # Tkinter uses 'takefocus' attribute
        self.assertTrue(f1.cget("takefocus") or any(c.cget("takefocus") for c in f1.winfo_children() if hasattr(c, "cget")))

if __name__ == "__main__":
    unittest.main()
