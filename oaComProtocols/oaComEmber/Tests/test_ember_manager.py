# oaComProtocols.oaComEmber/Tests/test_ember_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.1
#
# Description: Unit tests for EmberManager ensuring Hub-and-Spoke integrity, 
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch

# --- Target Module ---
from oaComProtocols.oaComEmber.Entry import get_manager, EmberManager

class TestEmberManager(unittest.TestCase):
    """
    Architectural Integrity Tests for Ember+ Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and manager in isolation."""
        self.mock_state_cache = MagicMock()
        self.mock_mqtt = MagicMock()
        
        # Build the manager
        self.manager = EmberManager(
            state_cache_manager=self.mock_state_cache,
            mqtt_connection_manager=self.mock_mqtt
        )

    def test_lifecycle(self):
        """CHECK: Verify start/stop cycle."""
        # OPERATE
        self.manager.start()
        # CHECK
        self.assertTrue(self.manager.running)
        
        # OPERATE
        self.manager.stop()
        # CHECK
        self.assertFalse(self.manager.running)

    def test_connection_logic(self):
        """OPERATE: Simulate connecting to an external Spoke."""
        self.manager.connect("192.168.1.50", 9000)
        
        # CHECK
        status = self.manager.get_status()
        self.assertEqual(status["connection"], "192.168.1.50:9000")
        self.assertTrue(status["running"])

    def test_telemetry_notifications(self):
        """CHECK: Verify monitor callbacks are triggered for GUI sync."""
        # BUILD
        mock_callback = MagicMock()
        self.manager.add_monitor_callback(mock_callback)
        
        # OPERATE
        self.manager._trigger_callbacks("RX", "node/volume", 0.5)
        
        # CHECK
        mock_callback.assert_called_with("RX", "node/volume", 0.5, None)

if __name__ == "__main__":
    unittest.main()
