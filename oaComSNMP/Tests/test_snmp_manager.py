# Tests/test_snmp_manager.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
from oaComSNMP.Managers.snmp_manager import SNMPManager, BridgeContext

class TestSNMPManager(unittest.TestCase):
    def setUp(self):
        self.state_cache = MagicMock()
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
            context = BridgeContext(state_cache_manager=self.state_cache)
            self.manager = SNMPManager.create(context, run_bridge=True)

    def test_initialization(self):
        """Goal: Verify that SNMPManager initializes with correct default state."""
        self.assertFalse(self.manager._running)
        self.assertEqual(len(self.manager._monitor_callbacks), 0)

    @patch("threading.Thread")
    def test_start_sequence(self, mock_thread):
        """Goal: Verify that starting the manager sets the running flag."""
        self.manager.start()
        self.assertTrue(self.manager._running)

    def test_add_monitor_callback(self):
        """Goal: Verify that GUI monitor callbacks can be registered."""
        callback = MagicMock()
        self.manager.add_monitor_callback(callback)
        self.assertIn(callback, self.manager._monitor_callbacks)

if __name__ == "__main__":
    unittest.main()
