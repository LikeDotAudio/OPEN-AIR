# oaComProtocols.oaComAES70/Tests/test_aes70_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.1
#
# Description: Unit tests for AES70Manager ensuring Hub-and-Spoke integrity,
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock

# --- Target Module ---
from oaComProtocols.oaComAES70.Core.aes70 import AES70Manager


class TestAES70Manager(unittest.TestCase):
    """
    Architectural Integrity Tests for AES70 Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and manager in isolation."""
        self.mock_state_cache = MagicMock()

        # Build the manager
        self.manager = AES70Manager(state_cache_manager=self.mock_state_cache, run_bridge=True)

    def tearDown(self):
        """Cleanup."""
        self.manager.stop()

    def test_lifecycle(self):
        """CHECK: Verify start/stop cycle."""
        self.manager.start()
        self.assertTrue(self.manager._running)
        self.manager.stop()
        self.assertFalse(self.manager._running)

    def test_spoke_to_hub_ingest(self):
        """OPERATE: Simulate incoming AES70 data (Spoke -> Hub)."""
        # BUILD
        test_data = b"\x3b\x32\x00\x00\x00\x01" # Mock PDU data
        mock_pdu = {"version": 1, "message_count": 1, "messages": [{"handle": 1, "target_ono": 1, "method_id": 1}]}
        self.manager._parser.decode = MagicMock(return_value=mock_pdu)
        self.manager._handle_message = MagicMock()

        # OPERATE
        self.manager.ingest_pdu(test_data)

        # CHECK: Data passed to handler
        self.manager._handle_message.assert_called_once()

    def test_telemetry_notifications(self):
        """CHECK: Verify monitor callbacks are triggered for GUI sync."""
        # BUILD
        mock_callback = MagicMock()
        self.manager.add_monitor_callback(mock_callback)

        # OPERATE
        self.manager.trigger_scan()

        # CHECK
        mock_callback.assert_called_with("SCAN_COMPLETE", unittest.mock.ANY)

if __name__ == "__main__":
    unittest.main()
