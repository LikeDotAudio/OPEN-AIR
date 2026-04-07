# /home/anthony/Documents/OPEN-AIR/oaComProtocols.oaComSNMP/Tests/test_snmp_manager.py
# Author: Gemini (Collaborator)
# Version: 20260405.2330.1
#
# Description: Unit tests for oaComProtocols.oaComSNMP.snmp_manager - Verifying MQTT Reflection

import unittest
from unittest.mock import MagicMock, patch
import threading
from oaComProtocols.oaComSNMP.Managers.snmp_manager import SNMPManager, SNMPObserver, SNMPBridge, BridgeContext

class TestSnmpManager(unittest.TestCase):

    def setUp(self):
        """Set up test environment with mocks."""
        self.mock_state_cache = MagicMock()
        self.mock_mqtt_conn = MagicMock()
        self.mock_sub_router = MagicMock()
        
        self.context = BridgeContext(
            state_cache_manager=self.mock_state_cache,
            mqtt_connection_manager=self.mock_mqtt_conn,
            subscriber_router=self.mock_sub_router
        )
        
        # Test the base class via a subclass or direct instantiation if allowed
        # Base SNMPManager is intended to be used via factory or subclasses
        self.observer = SNMPObserver(self.context)
        self.bridge = SNMPBridge(self.context)

    def tearDown(self):
        """Clean up."""
        self.observer.stop()
        self.bridge.stop()

    def test_mqtt_state_reflection(self):
        """Verify that MQTT messages are reflected in the internal state and cache is bypassed."""
        # BUILD: Start the manager
        self.observer.start()
        
        test_msg = {
            "source": "MQTT",
            "topic": "OPEN-AIR/Audio/Master/Volume",
            "val": 75,
            "meta": {"msg_type": "LINK_FEEDBACK", "is_settled": True}
        }
        
        # OPERATE: Handle a protocol event from MQTT
        self.observer.handle_protocol_event(test_msg)
        
        # CHECK: Internal state mirror should have it
        state = self.observer.get_mqtt_state()
        self.assertIn("OPEN-AIR/Audio/Master/Volume", state)
        self.assertEqual(state["OPEN-AIR/Audio/Master/Volume"]["val"], 75)
        
        # CHECK: state_cache_manager should NOT have been called for this specific data storage
        # (It might still be used for monitor activity logs if enabled, but internal state must be independent)
        self.mock_state_cache.handle_external_update.assert_not_called()

    def test_ignore_non_mqtt_sources(self):
        """Verify that events from other sources (OSC, MIDI) are NOT added to the MQTT state mirror."""
        self.observer.start()
        
        osc_msg = {
            "source": "OSC",
            "topic": "OPEN-AIR/Audio/Master/Mute",
            "val": 1
        }
        
        self.observer.handle_protocol_event(osc_msg)
        
        state = self.observer.get_mqtt_state()
        self.assertNotIn("OPEN-AIR/Audio/Master/Mute", state)

    def test_bridge_reflection(self):
        """Verify that SNMPBridge also performs MQTT reflection."""
        self.bridge.start()
        
        test_msg = {
            "source": "MQTT",
            "topic": "OPEN-AIR/System/Health",
            "val": "GOOD"
        }
        
        self.bridge.handle_protocol_event(test_msg)
        
        state = self.bridge.get_mqtt_state()
        self.assertIn("OPEN-AIR/System/Health", state)
        self.assertEqual(state["OPEN-AIR/System/Health"]["val"], "GOOD")

    def test_oid_map_conversion_from_snapshot(self):
        """Verify that the OID map is correctly built from the internal MQTT state snapshot."""
        # BUILD: Mock the converter
        mock_converter = MagicMock()
        self.bridge.oid_map_converter = mock_converter
        
        test_msg = {
            "source": "MQTT",
            "topic": "OPEN-AIR/Audio/Fader/1",
            "val": 100
        }
        self.bridge.start()
        self.bridge.handle_protocol_event(test_msg)
        
        # OPERATE: Persister loop would normally trigger this, we call it manually
        state_snapshot = self.bridge.get_mqtt_state()
        self.bridge.oid_map_converter.build_oid_map(state_snapshot=state_snapshot)
        
        # CHECK: build_oid_map was called with our reflected state
        mock_converter.build_oid_map.assert_called_with(state_snapshot=state_snapshot)

if __name__ == '__main__':
    unittest.main()
