# oaStateCache/Tests/test_rust_state_cache.py
#
# Tests for the State Cache (Python vs Rust).
#
# Author: Anthony Peter Kuzub
# Version: 20260331.1850.1

import unittest
from unittest.mock import MagicMock, patch
from oaStateCache.Core.state_cache import StateRegistry

class TestRustStateCache(unittest.TestCase):
    def setUp(self):
        self.mqtt = MagicMock()

    @patch("oaConfiguration.FileReaders.config_reader.Config.get_boolean")
    def test_compare_python_vs_rust_state_cache(self, mock_get_boolean):
        # 1. Run Python
        mock_get_boolean.return_value = False
        with patch("oaStateCache.Core.state_cache.cache_io_handler.load_cache", return_value={}):
            registry_py = StateRegistry(self.mqtt)
        
        self.assertIsNone(registry_py.rust_cache)
        
        # 2. Run Rust
        mock_get_boolean.return_value = True
        try:
            import oastateregistry_rs
            with patch("oaStateCache.Core.state_cache.cache_io_handler.load_cache", return_value={}):
                registry_rs = StateRegistry(self.mqtt)
            self.assertIsNotNone(registry_rs.rust_cache)
        except ImportError:
            self.skipTest("Rust oastateregistry_rs not installed.")

        # 3. Simulate Update
        topic = "TEST/RUST/TOPIC"
        val = {"val": 42, "status": "OK"}
        
        with patch("oaTranslator.Core.manifest.builder.create_manifest", return_value=val):
            with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
                registry_py.handle_external_update(topic, 42)
                registry_rs.handle_external_update(topic, 42)
        
        # 4. Compare Results
        self.assertEqual(registry_py.get_cached_value(topic), 42)
        self.assertEqual(registry_rs.get_cached_value(topic), 42)
        
        # Check Rust-specific dict export
        self.assertEqual(registry_rs.rust_cache.to_dict()[topic], val)

if __name__ == "__main__":
    unittest.main()
