# oaComProtocols.oaComSNMP/Tests/test_snmp_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260414.225.1
#
# Description: Unit tests for 100% Independent SNMPManager.

import unittest
from unittest.mock import MagicMock, patch

# --- Target Module ---
from oaComProtocols.oaComSNMP.Managers.snmp_manager import BridgeContext, SNMPBridge


class TestSnmpManager(unittest.TestCase):
    """
    Architectural Integrity Tests for Standalone SNMP Protocol Spoke.
    """

    def setUp(self):
        """BUILD: Initialize mocks and manager in isolation."""
        self.mock_mqtt_client = MagicMock()

        self.context = BridgeContext(
            mqtt_client=self.mock_mqtt_client
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
        """Cleanup."""
        self.bridge.stop()
        self.patcher_persister.stop()
        self.patcher_monitor.stop()

    def test_mqtt_reflection(self):
        """OPERATE: Verify that MQTT events are reflected in local SNMP state."""
        # BUILD
        test_topic = "OPEN-AIR/Audio/Master/Volume"
        test_val = 85

        # OPERATE
        self.bridge.handle_mqtt_message(test_topic, {"value": test_val})

        # CHECK: Local state mirror is updated
        state = self.bridge.get_mqtt_state()
        self.assertIn(test_topic, state)
        self.assertEqual(state[test_topic]["value"], test_val)

    def test_anti_feedback_echo_suppression(self):
        """CHECK: Verify messages originating from SNMP are NOT reflected back to local state."""
        # BUILD
        test_topic = "OPEN-AIR/Audio/Fader/1"
        payload = {
            "value": 100,
            "origin_source": "SNMP" # SELF source
        }

        # OPERATE
        self.bridge.handle_mqtt_message(test_topic, payload)

        # CHECK: Dropped (not in local state mirror)
        state = self.bridge.get_mqtt_state()
        self.assertNotIn(test_topic, state)

    def test_telemetry_broadcast(self):
        """CHECK: Verify status is published to the system tree."""
        # OPERATE
        self.bridge._publish_status()

        # CHECK: Verify publication to system status tree via native client
        self.mock_mqtt_client.publish.assert_called()

        found = False
        for call in self.mock_mqtt_client.publish.call_args_list:
            args, kwargs = call
            # Handle positional or keyword 'topic'
            topic = args[0] if len(args) > 0 else kwargs.get('topic')
            if topic == "OPEN-AIR/System/Status/SNMP/Bridge":
                found = True
                break
        self.assertTrue(found, "Status topic not found in publish calls.")

    def test_run_verification_delegation(self):
        """CHECK: Verify run_verification correctly delegates to SnmpTester."""
        # BUILD
        test_mib = "/tmp/test.mib"

        # OPERATE: Patch SnmpTester to avoid subprocess execution
        with patch("oaComProtocols.oaComSNMP.Workers.snmp_tester.SnmpTester.verify_oid_tree") as mock_tester:
            mock_tester.return_value = "SUCCESS"

            output = self.bridge.run_verification(mib_path=test_mib)

            # CHECK
            mock_tester.assert_called_once_with(base_oid=self.bridge.base_oid, mib_path=test_mib)
            self.assertEqual(output, "SUCCESS")

if __name__ == '__main__':
    unittest.main()
