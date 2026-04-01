# oaComBroker/Tests/test_rust_router.py
#
# Tests for the Protocol Router (Rust implementation).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import unittest
from unittest.mock import MagicMock, patch
from oaComBroker.Core.protocol_router.manager import ProtocolRouter

class TestRustRouter(unittest.TestCase):
    def setUp(self):
        # Reset singleton for testing
        ProtocolRouter._instance = None

    def test_rust_router_ingest(self):
        """Test ingestion with the Rust-backed router."""
        try:
            import oacorerouter_rs
        except ImportError:
            self.skipTest("Rust oacorerouter_rs not installed.")

        router = ProtocolRouter.get_instance(force_reload=True)
        self.assertIsNotNone(router.rust_router)
        
        # Test ingestion
        router.ingest("MQTT", "test/rs", 200)
        
        # Verify it went into the rust router
        # Note: We assume oacorerouter_rs.CoreRouter has inbound_len() and pop_inbound()
        # as suggested by the previous version of this test.
        self.assertEqual(router.rust_router.inbound_len(), 1)
        msg_rs = router.rust_router.pop_inbound()
        self.assertEqual(msg_rs["topic"], "test/rs")
        self.assertEqual(msg_rs["val"], 200)

if __name__ == "__main__":
    unittest.main()
