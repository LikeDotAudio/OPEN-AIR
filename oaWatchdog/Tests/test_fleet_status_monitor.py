# oaWatchdog/Tests/test_fleet_status_monitor.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the FleetStatusMonitor class.

import unittest
from unittest.mock import MagicMock, patch
import orjson
import time

from oaWatchdog.Managers.fleet_status_monitor import FleetStatusMonitor
from oaComMQTT.Core.mqtt_message import MqttMessage

class TestFleetStatusMonitor(unittest.TestCase):

    def setUp(self):
        """Set up the mock subscriber router and the FleetStatusMonitor instance."""
        self.mock_sme = MagicMock()
        self.mock_router = MagicMock()
        
        # Patch publish_payload before instantiation as __init__ calls _publish_color
        self.patcher = patch('oaWatchdog.Managers.fleet_status_monitor.publish_payload')
        self.mock_publish = self.patcher.start()
        
        self.monitor = FleetStatusMonitor(
            state_mirror_engine=self.mock_sme,
            subscriber_router=self.mock_router
        )

    def tearDown(self):
        self.patcher.stop()

    def test_initialization_and_subscription(self):
        """
        BUILD: Instantiate FleetStatusMonitor (done in setUp).
        OPERATE: Check initialization state.
        CHECK: Assert subscriptions to Start and Complete topics and initial RED publish.
        """
        base = "OPEN-AIR/System/Status/Fleet"
        self.mock_router.subscribe_to_topic.assert_any_call(f"{base}/Start", self.monitor._on_scan_start)
        self.mock_router.subscribe_to_topic.assert_any_call(f"{base}/Complete", self.monitor._on_scan_complete)
        
        # Initial publish during __init__
        self.mock_publish.assert_called_once()
        args, _ = self.mock_publish.call_args
        self.assertEqual(args[0], "OPEN-AIR/GUI/Global/Header/StatusLight")
        payload = orjson.loads(args[1])
        self.assertEqual(payload["color"], "red")

    def test_on_scan_start(self):
        """
        BUILD: Monitor in GREEN state.
        OPERATE: Call _on_scan_start.
        CHECK: Assert state changes to RED and publishes red.
        """
        self.monitor.current_state = "GREEN"
        self.mock_publish.reset_mock()
        
        msg = MqttMessage(topic="OPEN-AIR/System/Status/Fleet/Start", payload=b"{}")
        self.monitor._on_scan_start(msg)
        
        self.assertEqual(self.monitor.current_state, "RED")
        args, _ = self.mock_publish.call_args
        payload = orjson.loads(args[1])
        self.assertEqual(payload["color"], "red")

    def test_on_scan_complete_with_devices(self):
        """
        BUILD: Monitor in RED state.
        OPERATE: Call _on_scan_complete with num_devices > 0.
        CHECK: Assert state changes to GREEN and publishes green.
        """
        self.monitor.current_state = "RED"
        self.mock_publish.reset_mock()
        
        data = {"num_devices": 5}
        msg = MqttMessage(topic="OPEN-AIR/System/Status/Fleet/Complete", payload=orjson.dumps(data))
        self.monitor._on_scan_complete(msg)
        
        self.assertEqual(self.monitor.current_state, "GREEN")
        args, _ = self.mock_publish.call_args
        payload = orjson.loads(args[1])
        self.assertEqual(payload["color"], "green")

    def test_on_scan_complete_no_devices(self):
        """
        BUILD: Monitor in GREEN state.
        OPERATE: Call _on_scan_complete with num_devices == 0.
        CHECK: Assert state changes to RED and publishes red.
        """
        self.monitor.current_state = "GREEN"
        self.mock_publish.reset_mock()
        
        data = {"num_devices": 0}
        msg = MqttMessage(topic="OPEN-AIR/System/Status/Fleet/Complete", payload=orjson.dumps(data))
        self.monitor._on_scan_complete(msg)
        
        self.assertEqual(self.monitor.current_state, "RED")
        args, _ = self.mock_publish.call_args
        payload = orjson.loads(args[1])
        self.assertEqual(payload["color"], "red")

    def test_on_scan_complete_malformed_payload(self):
        """
        BUILD: Monitor in GREEN state.
        OPERATE: Call _on_scan_complete with invalid JSON.
        CHECK: Assert it defaults back to RED safely.
        """
        self.monitor.current_state = "GREEN"
        self.mock_publish.reset_mock()
        
        msg = MqttMessage(topic="OPEN-AIR/System/Status/Fleet/Complete", payload=b"invalid json")
        self.monitor._on_scan_complete(msg)
        
        self.assertEqual(self.monitor.current_state, "RED")
        args, _ = self.mock_publish.call_args
        payload = orjson.loads(args[1])
        self.assertEqual(payload["color"], "red")

if __name__ == '__main__':
    unittest.main()
