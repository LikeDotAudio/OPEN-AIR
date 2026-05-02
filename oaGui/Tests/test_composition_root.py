# oaGui/Tests/test_loader_service_composer.py
# Author: Gemini CLI
# Version: 20260404.1.1
#
# Description: Unit tests for loader_service_composer.py

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGui.Managers.orchestration.loader_service_composer import LoaderServiceComposer


class TestUICompositionRoot(unittest.TestCase):
    """Verifies that the UI composition root correctly wires dependencies."""

    def setUp(self):
        """Build mock root and constants."""
        self.mock_root = MagicMock(spec=tk.Tk)
        self.mock_constants = MagicMock()
        self.mock_constants.SCAN_OSC = True
        self.mock_constants.SCAN_SNMP = False

        self.comp_root = LoaderServiceComposer(self.mock_root, self.mock_constants)

    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_connection.MqttConnectionManager')
    @patch('oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router.MqttSubscriberRouter')
    @patch('oaStateCache.Core.state_cache.StateRegistry')
    @patch('oaStateCache.Core.state_mirror_engine.StateMirrorEngine')
    @patch('oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance')
    @patch('oaComProtocols.oaComOSC.Managers.osc_manager.OSCManager')
    @patch('oaComProtocols.oaComREST.Managers.rest_manager.RESTManager')
    @patch('oaSplinker.Core.splinker.ControlBroker.get_instance')
    def test_build_services_wires_all_layers(self, mock_splinker, mock_rest, mock_osc, mock_proto_get, mock_mirror, mock_cache, mock_router, mock_mqtt):
        """OPERATE: Build services. CHECK: Verify service graph is constructed and mapped."""
        services = self.comp_root.build_services()

        # Verify base layers exist in the returned dictionary
        self.assertIn("mqtt_conn", services)
        self.assertIn("state_cache", services)
        self.assertIn("mirror_engine", services)

        # Verify wiring
        # state_cache should have been set with the sub_router instance
        # Since they are all mocks, we check if the sub_router mock was assigned to the cache mock
        self.assertEqual(services["state_cache"].subscriber_router, services["sub_router"])

        # Verify OSC was enabled (as SCAN_OSC = True)
        self.assertIn("osc_manager", services)

if __name__ == '__main__':
    unittest.main()
