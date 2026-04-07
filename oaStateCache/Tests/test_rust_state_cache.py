# oaStateCache/Tests/test_rust_state_cache.py
#
# Tests for the State Cache (Rust implementation).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import unittest
from unittest.mock import MagicMock, patch
from oaStateCache.Core.state_cache import StateRegistry

class TestRustStateCache(unittest.TestCase):
    def setUp(self):
        self.mqtt = MagicMock()

    def test_rust_state_cache_initialization(self):
        """Test that StateRegistry initializes the Rust core."""
        try:
            import oastateregistry_rs
        except ImportError:
            self.skipTest("Rust oastateregistry_rs not installed.")

        with patch("oaStateCache.Core.state_cache.cache_io_handler.load_cache", return_value={}):
            registry = StateRegistry(self.mqtt)
        
        self.assertIsNotNone(registry.rust_cache)

    def test_rust_state_cache_update(self):
        """Test state update with the Rust-backed registry."""
        try:
            import oastateregistry_rs
        except ImportError:
            self.skipTest("Rust oastateregistry_rs not installed.")

        with patch("oaStateCache.Core.state_cache.cache_io_handler.load_cache", return_value={}):
            registry = StateRegistry(self.mqtt)

        topic = "TEST/RUST/TOPIC"
        val = {"val": 42, "status": "OK"}
        
        with patch("oaStateCache.Core.manifest.builder.create_manifest", return_value=val):
            with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
                registry.handle_external_update(topic, 42)
        
        # Verify results
        self.assertEqual(registry.get_cached_value(topic), 42)
        # Check Rust-specific dict export
        self.assertEqual(registry.rust_cache.to_dict()[topic], val)

if __name__ == "__main__":
    unittest.main()
