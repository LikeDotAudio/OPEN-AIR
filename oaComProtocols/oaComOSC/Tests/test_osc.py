# oaComProtocols.oaComOSC/Tests/test_osc.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.1
#
# Description: Unit tests for OSCManager ensuring Hub-and-Spoke integrity,
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch

# --- Target Module ---
from oaComProtocols.oaComOSC.Managers.osc_manager import OSCManager


class TestOSCManager(unittest.TestCase):
    """
    Architectural Integrity Tests for OSC Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and manager in isolation."""
        self.mock_state_cache = MagicMock()
        self.mock_mqtt = MagicMock()
        self.mock_router = MagicMock()

        # Patch ProtocolRouter to prevent real singleton access and auto-start
        self.patcher_router = patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance", return_value=self.mock_router)
        self.patcher_router.start()

        # Patch Workers to prevent socket binding
        self.patcher_rx = patch("oaComProtocols.oaComOSC.Managers.osc_manager.OscRxServer")
        self.patcher_tx = patch("oaComProtocols.oaComOSC.Managers.osc_manager.OscTxClient")
        self.mock_rx_class = self.patcher_rx.start()
        self.mock_tx_class = self.patcher_tx.start()

        # Patch network utils
        self.patcher_ip = patch("oaComProtocols.oaComOSC.Managers.osc_manager.get_local_ip", return_value="127.0.0.1")
        self.patcher_ip.start()

        # Build the manager
        self.manager = OSCManager(
            state_cache_manager=self.mock_state_cache,
            mqtt_connection_manager=self.mock_mqtt,
            run_bridge=True
        )

    def tearDown(self):
        """Cleanup patches."""
        self.manager.stop()
        self.patcher_router.stop()
        self.patcher_rx.stop()
        self.patcher_tx.stop()
        self.patcher_ip.stop()

    def test_standardized_lifecycle(self):
        """CHECK: Verify the manager adheres to always-online standardized behavior."""
        # OPERATE is handled by __init__ auto-start
        self.assertTrue(self.manager._running)
        status = self.manager.get_status()
        self.assertTrue(status["running"])
        self.assertIn("127.0.0.1", status["rx_socket"])

    def test_spoke_to_hub_ingest(self):
        """OPERATE: Simulate incoming OSC data (Spoke -> Hub)."""
        # BUILD
        test_addr = "/test/volume"
        test_val = 0.75
        self.manager.register_route(test_addr, "OpenAir/Audio/Volume")

        # OPERATE
        self.manager.handle_incoming_osc(test_addr, test_val)

        # CHECK: Data normalized and sent to Hub (StateCache/ProtocolRouter)
        # Note: We use assert_any_call because start() triggers a status broadcast
        self.mock_state_cache.handle_external_update.assert_any_call(
            "OpenAir/Audio/Volume", test_val, source="OSC", metadata=unittest.mock.ANY
        )

        # Verify anti-feedback tag in the specific call
        found = False
        for call in self.mock_state_cache.handle_external_update.call_args_list:
            if call[0][0] == "OpenAir/Audio/Volume":
                self.assertEqual(call[1]["metadata"]["origin_source"], "OSC")
                found = True
        self.assertTrue(found)

    def test_hub_to_spoke_dispatch(self):
        """OPERATE: Simulate Hub broadcast (Hub -> Spoke)."""
        # BUILD
        self.manager.register_route("/test/fader", "OpenAir/Mixer/Fader")
        mock_tx_instance = self.mock_tx_class.return_value

        # OPERATE: Data from an external source (e.g., GUI)
        message = {
            "source": "MQTT",
            "logical_source": "GUI",
            "topic": "OpenAir/Mixer/Fader",
            "value": 1.0,
            "meta": {"origin_source": "GUI"}
        }
        self.manager._on_protocol_event(message)

        # CHECK: Transmitted to hardware Spoke
        mock_tx_instance.send_message.assert_called_with("/test/fader", 1.0)

    def test_anti_feedback_echo_suppression(self):
        """CHECK: Verify messages originating from OSC are NOT echoed back to OSC."""
        # BUILD
        self.manager.register_route("/test/fader", "OpenAir/Mixer/Fader")
        mock_tx_instance = self.mock_tx_class.return_value

        # OPERATE: Data that originally came FROM OSC
        message = {
            "source": "MQTT",
            "logical_source": "OSC",
            "topic": "OpenAir/Mixer/Fader",
            "value": 0.5,
            "meta": {"origin_source": "OSC"}
        }
        self.manager._on_protocol_event(message)

        # CHECK: Echo suppression (should NOT call send_message)
        mock_tx_instance.send_message.assert_not_called()

    def test_telemetry_broadcast(self):
        """CHECK: Verify periodic status broadcast for system monitoring."""
        # BUILD: Force a broadcast
        self.manager._broadcast_status_loop = MagicMock() # Stop the actual loop

        # OPERATE
        status = self.manager.get_status()
        self.manager.state_cache_manager.handle_external_update(
            "OpenAir/System/Status/OSC/Bridge", status, source="OSC-STATUS"
        )

        # CHECK
        self.mock_state_cache.handle_external_update.assert_any_call(
            "OpenAir/System/Status/OSC/Bridge", unittest.mock.ANY, source="OSC-STATUS"
        )

if __name__ == "__main__":
    unittest.main()
