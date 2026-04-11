# oaComProtocols.oaComSMPTE2138/Tests/test_smpte2138_bridge.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.3
#
# Description: Unit tests for SMPTE2138BridgeManager ensuring Hub-and-Spoke integrity, 
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch

# --- Target Module ---
from oaComProtocols.oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager

class TestSMPTE2138Bridge(unittest.TestCase):
    """
    Architectural Integrity Tests for SMPTE ST 2138 Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and manager in isolation."""
        self.mock_mqtt = MagicMock()
        self.mock_router = MagicMock()
        
        # Build the manager
        self.manager = SMPTE2138BridgeManager(
            mqtt_connection=self.mock_mqtt,
            subscriber_router=self.mock_router
        )
        # ⚡ CRITICAL: Reset mock because __init__ calls _publish_bridge_status()
        self.mock_mqtt.publish.reset_mock()

    def test_hub_to_spoke_dispatch(self):
        """OPERATE: Simulate Hub broadcast (Hub -> Spoke)."""
        # BUILD
        test_topic = "oa/action/sig_gen/frequency"
        test_val = 440.0
        
        # OPERATE: Data from an external source (e.g., GUI)
        self.manager.handle_router_event(test_topic, test_val, {"origin_source": "GUI"})
        
        # CHECK: Transmitted to hardware Spoke (ST2138 Protobuf via MQTT)
        self.mock_mqtt.publish.assert_called()
        
        # Verify it wasn't just the status broadcast
        found_data = False
        for call in self.mock_mqtt.publish.call_args_list:
            if "st2138/device/" in call.kwargs.get('topic', ''):
                found_data = True
                break
        self.assertTrue(found_data)

    def test_anti_feedback_echo_suppression(self):
        """CHECK: Verify messages originating from SMPTE2138 are NOT echoed back."""
        # BUILD
        test_topic = "oa/action/sig_gen/frequency"
        
        # OPERATE: Data that originally came FROM SMPTE2138
        self.manager.handle_router_event(test_topic, 440.0, {"origin_source": "SMPTE2138"})
        
        # CHECK: Echo suppression
        self.mock_mqtt.publish.assert_not_called()

    def test_telemetry_broadcast(self):
        """CHECK: Verify periodic status broadcast for system monitoring."""
        # OPERATE
        self.manager._publish_bridge_status()
        
        # CHECK: Verify publication to system status tree
        self.mock_mqtt.publish.assert_called()
        args, kwargs = self.mock_mqtt.publish.call_args
        # Handle both positional and keyword 'topic'
        topic = kwargs.get('topic') or (args[0] if args else None)
        self.assertEqual(topic, "OPEN-AIR/System/Status/SMPTE2138/Bridge")

if __name__ == "__main__":
    unittest.main()
