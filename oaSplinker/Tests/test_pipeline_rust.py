# oaSplinker/Tests/test_pipeline_rust.py
#
# Tests for the SplinkPipeline (Rust implementation).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1100.1

import unittest
from unittest.mock import MagicMock, patch
from oaSplinker.Methods.pipeline import SplinkPipeline

class TestPipelineRust(unittest.TestCase):
    def setUp(self):
        self.splinker_manager = MagicMock()
        self.splink_config = {
            "id": "test_splink",
            "label": "Test Splink",
            "source": "source",
            "destination": "destination",
            "handlers": [
                {
                    "type": "scale",
                    "enabled": True,
                    "params": {
                        "source_min": 0,
                        "source_max": 100,
                        "destination_min": 0,
                        "destination_max": 255
                    }
                }
            ]
        }

    def test_rust_scale(self):
        """Test the Rust SplinkPipeline with scale handler."""
        try:
            from oaRustCore.oa_splink_core_rs import SplinkPipeline as RustSplinkPipeline
        except ImportError:
            self.skipTest("Rust oasplinkcore_rs not installed.")

        pipeline = SplinkPipeline(self.splink_config, self.splinker_manager)
        self.assertIsNotNone(pipeline.rust_pipeline)
        
        # Test scale (50 / 100 * 255 = 127.5)
        out = pipeline.process(50, {})
        self.assertEqual(out, 127.5)

    def test_deadband_state_rust(self):
        """Test the Rust SplinkPipeline with deadband handler."""
        try:
            from oaRustCore.oa_splink_core_rs import SplinkPipeline as RustSplinkPipeline
        except ImportError:
            self.skipTest("Rust oasplinkcore_rs not installed.")

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
        
        pipeline = SplinkPipeline(self.splink_config, self.splinker_manager)
        self.assertIsNotNone(pipeline.rust_pipeline)
        
        state = {}
        # First value passes
        self.assertEqual(pipeline.process(50, state), 50)
        self.assertEqual(state.get("last_deadband_value"), 50)
        
        # Change by 4% (less than 10%) -> should drop (return None)
        self.assertIsNone(pipeline.process(54, state))
        self.assertEqual(state.get("last_deadband_value"), 50)
        
        # Change by 15% (more than 10%) -> should pass
        self.assertEqual(pipeline.process(66, state), 66)
        self.assertEqual(state.get("last_deadband_value"), 66)

if __name__ == "__main__":
    unittest.main()
