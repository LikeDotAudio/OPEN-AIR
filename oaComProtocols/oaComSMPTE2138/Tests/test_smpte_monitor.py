import unittest
from unittest.mock import MagicMock
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_monitor_manager import SMPTE2138MonitorManager

class TestSMPTE2138MonitorManager(unittest.TestCase):
    def setUp(self):
        self.mqtt = MagicMock()
        self.router = MagicMock()
        self.manager = SMPTE2138MonitorManager(self.mqtt, self.router)

    def test_initialization(self):
        """Verify that the monitor manager initializes and subscribes."""
        self.assertIsNotNone(self.manager)
        # Check subscriptions
        self.router.subscribe_to_topic.assert_any_call("st2138/#", self.manager._on_smpte2138_traffic)

if __name__ == "__main__":
    unittest.main()
