# oaSplinker/Tests/test_pipeline_rust.py
#
# Tests for the SplinkPipeline (Python vs Rust).
#
# Author: Anthony Peter Kuzub
# Version: 20260331.1500.1

import unittest
from unittest.mock import MagicMock, patch
from oaSplinker.Methods.pipeline import SplinkPipeline
from oaConfiguration.Entry import Config

class TestPipelineRust(unittest.TestCase):
    def setUp(self):
        self.splinker_manager = MagicMock()
        self.splink_config = {
            "id": "test_splink",
            "label": "Test Splink",
            "source": "src",
            "dest": "dst",
            "handlers": [
                {
                    "type": "scale",
                    "enabled": True,
                    "params": {
                        "source_min": 0,
                        "source_max": 100,
                        "dest_min": 0,
                        "dest_max": 255
                    }
                }
            ]
        }

    @patch("oaConfiguration.Entry.Config.get_boolean")
    def test_compare_python_vs_rust_scale(self, mock_get_boolean):
        # 1. Test Python
        mock_get_boolean.return_value = False
        pipeline_py = SplinkPipeline(self.splink_config, self.splinker_manager)
        self.assertIsNone(pipeline_py.rust_pipeline)
        
        state = {}
        out_py = pipeline_py.process(50, state)
        self.assertEqual(out_py, 128) # round(0 + (50/100)*255) = 127.5 -> 128

        # 2. Test Rust
        mock_get_boolean.return_value = True
        pipeline_rs = SplinkPipeline(self.splink_config, self.splinker_manager)
        
        # If Rust is available, this should be set
        try:
            from oasplinkcore_rs import SplinkPipeline as RustSplinkPipeline
            self.assertIsNotNone(pipeline_rs.rust_pipeline)
            out_rs = pipeline_rs.process(50, state)
            self.assertEqual(out_rs, 128)
            self.assertEqual(out_py, out_rs)
        except ImportError:
            self.skipTest("Rust oasplinkcore_rs not installed.")

    @patch("oaConfiguration.Entry.Config.get_boolean")
    def test_deadband_state_rust(self, mock_get_boolean):
        mock_get_boolean.return_value = True
        self.splink_config["handlers"] = [
            {
                "type": "deadband",
                "enabled": True,
                "params": {
                    "threshold_percent": 10,
                    "max_value": 100
                }
            }
        ]
        
        try:
            pipeline = SplinkPipeline(self.splink_config, self.splinker_manager)
            if not pipeline.rust_pipeline:
                self.skipTest("Rust oasplinkcore_rs not installed or failed to init.")
            
            state = {}
            # First value passes
            self.assertEqual(pipeline.process(50, state), 50)
            self.assertEqual(state.get("last_deadband_value"), 50)
            
            # Change by 5% (less than 10%) -> should drop (None)
            self.assertIsNone(pipeline.process(54, state))
            self.assertEqual(state.get("last_deadband_value"), 50)
            
            # Change by 15% (more than 10%) -> should pass
            self.assertEqual(pipeline.process(66, state), 66)
            self.assertEqual(state.get("last_deadband_value"), 66)
            
        except ImportError:
            self.skipTest("Rust oasplinkcore_rs not installed.")

if __name__ == "__main__":
    unittest.main()
