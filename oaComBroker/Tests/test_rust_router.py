# oaComBroker/Tests/test_rust_router.py
#
# Tests for the Protocol Router (Python vs Rust).
#
# Author: Anthony Peter Kuzub
# Version: 20260331.1910.1

import unittest
from unittest.mock import MagicMock, patch
import queue
import time
from oaComBroker.Core.protocol_router.manager import ProtocolRouter

class TestRustRouter(unittest.TestCase):
    def setUp(self):
        # Reset singleton for testing
        ProtocolRouter._instance = None

    @patch("oaConfiguration.FileReaders.config_reader.Config.get_boolean")
    def test_compare_python_vs_rust_router_ingest(self, mock_get_boolean):
        # 1. Test Python
        mock_get_boolean.return_value = False
        router_py = ProtocolRouter.get_instance(force_reload=True)
        self.assertIsNone(router_py.rust_router)
        
        router_py.ingest("MQTT", "test/py", 100)
        self.assertFalse(router_py.inbound_queue.empty())
        msg_py = router_py.inbound_queue.get()
        self.assertEqual(msg_py["topic"], "test/py")

        # 2. Test Rust
        mock_get_boolean.return_value = True
        try:
            import oacorerouter_rs
            router_rs = ProtocolRouter.get_instance(force_reload=True)
            self.assertIsNotNone(router_rs.rust_router)
            
            router_rs.ingest("MQTT", "test/rs", 200)
            self.assertEqual(router_rs.rust_router.inbound_len(), 1)
            msg_rs = router_rs.rust_router.pop_inbound()
            self.assertEqual(msg_rs["topic"], "test/rs")
            self.assertEqual(msg_rs["val"], 200)
            
        except ImportError:
            self.skipTest("Rust oacorerouter_rs not installed.")

if __name__ == "__main__":
    unittest.main()
