# oaComProtocols.oaComSNMP/Tests/test_snmp_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.5
#
# Description: Unit tests for SNMPManager ensuring Hub-and-Spoke integrity, 
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch
import os

# --- Target Module ---
from oaComProtocols.oaComSNMP.Managers.snmp_manager import SNMPBridge, BridgeContext

class TestSnmpManager(unittest.TestCase):
    """
    Architectural Integrity Tests for SNMP Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and manager in isolation."""
        self.mock_state_cache = MagicMock()
        self.mock_mqtt_conn = MagicMock()
        self.mock_sub_router = MagicMock()
        
        self.context = BridgeContext(
            state_cache_manager=self.mock_state_cache,
            mqtt_connection_manager=self.mock_mqtt_conn,
            subscriber_router=self.mock_sub_router
        )
        
        # Patch Persister and LogMonitor to prevent thread starts/file IO
        self.patcher_persister = patch("oaComProtocols.oaComSNMP.Managers.snmp_manager.SnmpStatePersister")
        self.patcher_monitor = patch("oaComProtocols.oaComSNMP.Managers.snmp_manager.SnmpLogMonitor")
        self.patcher_persister.start()
        self.patcher_monitor.start()

        # Build the manager (Bridge variant)
        self.bridge = SNMPBridge(self.context)
        # Ensure it is running for event handling
        self.bridge._running = True

    def tearDown(self):
        """Cleanup patches."""
        self.bridge.stop()
        self.patcher_persister.stop()
        self.patcher_monitor.stop()

    def test_spoke_to_hub_reflection(self):
        """OPERATE: Verify that MQTT events (Hub) are reflected in local SNMP state (Spoke)."""
        # BUILD
        test_topic = "OPEN-AIR/Audio/Master/Volume"
        test_val = 85
        message = {
            "source": "MQTT",
            "topic": test_topic,
            "value": test_val,
            "meta": {"is_settled": True}
        }
        
        # OPERATE
        self.bridge.handle_protocol_event(message)
        
        # CHECK: Local state mirror is updated
        state = self.bridge.get_mqtt_state()
        self.assertIn(test_topic, state)
        self.assertEqual(state[test_topic]["value"], test_val)

    def test_anti_feedback_echo_suppression(self):
        """CHECK: Verify messages originating from SNMP are NOT reflected back to local state."""
        # BUILD
        test_topic = "OPEN-AIR/Audio/Fader/1"
        message = {
            "source": "MQTT",
            "topic": test_topic,
            "value": 100,
            "meta": {"origin_source": "SNMP"} # SELF source
        }
        
        # OPERATE
        self.bridge.handle_protocol_event(message)
        
        # CHECK: Dropped (not in local state mirror)
        state = self.bridge.get_mqtt_state()
        self.assertNotIn(test_topic, state)

    def test_telemetry_broadcast(self):
        """CHECK: Verify status is published to the system tree."""
        # OPERATE
        self.bridge._publish_status()
        
        # CHECK: Verify publication to system status tree
        self.mock_mqtt_conn.publish.assert_called()
        
        # Handle both positional and keyword arguments correctly
        found = False
        for call in self.mock_mqtt_conn.publish.call_args_list:
            args, kwargs = call
            topic = kwargs.get('topic') or (args[0] if args else None)
            if topic == "OPEN-AIR/System/Status/SNMP/Bridge":
                found = True
                break
        self.assertTrue(found)

if __name__ == '__main__':
    unittest.main()
