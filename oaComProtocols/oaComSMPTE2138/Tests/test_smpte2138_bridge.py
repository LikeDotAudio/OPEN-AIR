import unittest
from unittest.mock import MagicMock, patch
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager

class TestSMPTE2138Bridge(unittest.TestCase):
    def setUp(self):
        self.mqtt_connection = MagicMock()
        self.router = MagicMock()
        
        self.manager = SMPTE2138BridgeManager(
            mqtt_connection=self.mqtt_connection,
            subscriber_router=self.router
        )

    def test_echo_suppression_and_transmission(self):
        """Test that ST2138 Bridge prevents feedback loops."""
        self.manager.publish = MagicMock()
        
        # 1. Message from GUI (External source) should be published
        self.manager.handle_router_event("oa/action/sig_gen/frequency", 440.0, {"origin_source": "GUI"})
        
        # The bridge builds an OID internally and publishes to ST2138
        # We just verify it reached the underlying mqtt_connection.publish
        self.mqtt_connection.publish.assert_called()
        self.mqtt_connection.publish.reset_mock()
        
        # 2. Message from SMPTE2138 (Echo) should be dropped
        self.manager.handle_router_event("oa/action/sig_gen/frequency", 440.0, {"origin_source": "SMPTE2138"})
        self.mqtt_connection.publish.assert_not_called()

if __name__ == "__main__":
    unittest.main()
