# oaComProtocols.oaComVisa/Tests/test_visa_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.6
#
# Description: Unit tests for VisaManager ensuring Hub-and-Spoke integrity,
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch

import orjson

# --- Target Module ---
from oaComProtocols.oaComVisa.Managers.visa_manager import VisaManagerOrchestrator


class TestVisaManagerOrchestrator(unittest.TestCase):
    """
    Architectural Integrity Tests for VISA Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and orchestrator in isolation."""
        self.mock_mqtt = MagicMock()
        self.mock_sub_router = MagicMock()
        self.mock_client = MagicMock()
        self.mock_mqtt.get_client_instance.return_value = self.mock_client

        # Patch internal components EXCEPT VisaGuiPublisher to ensure it runs
        self.patchers = [
            patch('oaComProtocols.oaComVisa.Managers.visa_manager.VisaProxy'),
            patch('oaComProtocols.oaComVisa.Managers.visa_manager.VisaDeviceSearcher'),
            patch('oaComProtocols.oaComVisa.Managers.visa_manager.VisaConnector'),
            patch('oaComProtocols.oaComVisa.Managers.visa_manager.VisaDisconnector'),
            patch('oaComProtocols.oaComVisa.Managers.visa_manager.VisaMqttListener'),
            patch('oaComProtocols.oaComVisa.Managers.visa_manager.VisaResetManager'),
            patch('oaComProtocols.oaComVisa.Managers.visa_manager.VisaRebootManager')
        ]
        for p in self.patchers: p.start()

        self.manager = VisaManagerOrchestrator(
            mqtt_connection_manager=self.mock_mqtt,
            subscriber_router=self.mock_sub_router
        )

    def tearDown(self):
        """Cleanup patches."""
        for p in self.patchers: p.stop()

    def test_hub_to_spoke_telemetry(self):
        """CHECK: Verify the manager broadcasts its presence to the system Hub."""
        # OPERATE: Logic is in __init__ via gui_publisher.
        # It calls gui_publisher._publish_proxy_status("INITIALIZING")

        # CHECK
        self.mock_client.publish.assert_called()

        # Check if any call was to Proxy/Status
        found = False
        for call in self.mock_client.publish.call_args_list:
            args, kwargs = call
            topic = kwargs.get('topic') or (args[0] if args else None)
            if topic and "Proxy/Status" in topic:
                found = True
                break
        self.assertTrue(found)

    def test_anti_feedback_origin_tagging(self):
        """CHECK: Verify that publications to Hub include origin metadata."""
        # OPERATE
        self.manager.gui_publisher._publish_status("connected", True)

        # CHECK
        self.mock_client.publish.assert_called()
        found = False
        for call in self.mock_client.publish.call_args_list:
            args, kwargs = call
            payload_raw = kwargs.get('payload') or (args[1] if len(args) > 1 else None)
            if payload_raw:
                payload = orjson.loads(payload_raw)
                if payload.get("origin_source") == "VISA":
                    found = True
                    break
        self.assertTrue(found)

if __name__ == '__main__':
    unittest.main()
