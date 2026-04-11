# oaComProtocols.oaComNmos/Tests/test_nmos_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.2
#
# Description: Unit tests for NMOS Entry/Manager ensuring Hub-and-Spoke integrity, 
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch
import threading

# --- Target Module ---
from oaComProtocols.oaComNmos.Entry import start, stop, status, global_state

class TestNMOSManager(unittest.TestCase):
    """
    Architectural Integrity Tests for NMOS Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and reset global state."""
        # Reset global state for isolation
        global_state["RUNNING"] = False
        global_state["NODE_ID"] = None
        
        # Patch external dependencies
        # ⚡ CRITICAL: We patch HTTPServer in EVERY namespace it appears to be sure.
        self.patchers = [
            patch('oaComProtocols.oaComNmos.Entry.get_ip', return_value="127.0.0.1"),
            patch('oaComProtocols.oaComNmos.Entry.gen_id', return_value="test-uuid"),
            patch('oaComProtocols.oaComNmos.Entry.registration_manager'),
            patch('oaComProtocols.oaComNmos.Entry.HTTPServer'),
            patch('oaComProtocols.oaComNmos.Entry.connection_api.HTTPServer'),
            patch('oaComProtocols.oaComNmos.Interface.connection_api.HTTPServer'),
            patch('oaComProtocols.oaComNmos.Entry.sap_listener_worker'),
            patch('oaComProtocols.oaComNmos.Entry.heartbeat_worker'),
            patch('oaComProtocols.oaComNmos.Entry.print'), # Silence output
            patch('threading.Thread')
        ]
        for p in self.patchers:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        """Stop service."""
        stop()

    def test_standardized_lifecycle(self):
        """CHECK: Verify start/stop/status cycle."""
        # OPERATE
        start(registrar_url="http://mock-registry:4000")
        
        # CHECK
        curr_status = status()
        self.assertTrue(curr_status["running"])
        self.assertEqual(curr_status["registrar"], "http://mock-registry:4000")
        self.assertEqual(curr_status["node_id"], "test-uuid")
        
        # OPERATE
        stop()
        
        # CHECK
        self.assertFalse(status()["running"])

    def test_spoke_telemetry_registration(self):
        """CHECK: Verify the manager registers itself with the NMOS registry on start."""
        # OPERATE
        start()
        
        # CHECK: registration_manager was called
        from oaComProtocols.oaComNmos.Entry import registration_manager
        registration_manager.register_all_resources.assert_called()

if __name__ == "__main__":
    unittest.main()
