# oaComSMPTE2138/Tests/test_dynamic_slot_oid.py
#
# Verification test for dynamic slot and OID assignment in the SMPTE2138 bridge.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260330.1600.1

import os
import sys
import unittest
from unittest.mock import MagicMock
import orjson

# Ensure we can import the local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from oaComSMPTE2138.Managers.smpte2138_bridge_manager import SMPTE2138BridgeManager
from oaComSMPTE2138.Interface import param_pb2

class TestDynamicSlotOID(unittest.TestCase):
    def setUp(self):
        self.mock_mqtt = MagicMock()
        self.mock_router = MagicMock()
        self.bridge = SMPTE2138BridgeManager(self.mock_mqtt, self.mock_router)
        self.published = []
        
        def mock_publish(topic, payload, qos=0, retain=False):
            self.published.append((topic, payload))
        self.mock_mqtt.publish = mock_publish

    def test_dynamic_assignment(self):
        # 1. Prepare simulation data
        topic = "OPEN-AIR/Assets/Spectrum/Instrument/frequency/Spectrum_Instrument_frequency/blocks/Frequency/center_freq_MHz"
        value = 550.5
        metadata = {
            "bin_id": "50.100.0.3.1",
            "block_name": "Frequency",
            "field_name": "center_freq_MHz"
        }
        
        # 2. Trigger the bridge
        self.bridge.handle_router_event(topic, value, metadata)
        
        # 3. Verify results
        # We expect a publication to st2138/device/50100031/param/Frequency/center_freq_MHz
        expected_slot = 50100031
        expected_oid = "Frequency/center_freq_MHz"
        expected_topic = f"st2138/device/{expected_slot}/param/{expected_oid}"
        
        found = False
        for t, p in self.published:
            if t == expected_topic:
                found = True
                # Decode the protobuf payload
                payload = param_pb2.SingleSetValuePayload()
                payload.ParseFromString(p)
                
                self.assertEqual(payload.slot, expected_slot)
                self.assertEqual(payload.value.oid, expected_oid)
                self.assertEqual(payload.value.value.float32_value, value)
                break
        
        self.assertTrue(found, f"Expected topic {expected_topic} not found in published messages: {[m[0] for m in self.published]}")

    def test_fallback_assignment(self):
        # Verify that it falls back to static mapping if metadata is missing
        topic = "oa/action/sig_gen/frequency"
        value = 440.0
        
        self.bridge.handle_router_event(topic, value, None)
        
        expected_slot = 1
        expected_oid = "frequency"
        expected_topic = f"st2138/device/{expected_slot}/param/{expected_oid}"
        
        found = False
        for t, p in self.published:
            if t == expected_topic:
                found = True
                break
        
        self.assertTrue(found, "Fallback assignment failed")

if __name__ == "__main__":
    unittest.main()
