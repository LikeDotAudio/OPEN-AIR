# oaGuiManager/Tests/test_bootstrap_sequence.py
# Author: Gemini CLI
# Version: 20260404.1.6
#
# Description: Unit tests for bootstrap_sequence.py

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiManager.Core.bootstrap_sequence import AsyncBootstrapEngine

class TestAsyncBootstrapEngine(unittest.TestCase):
    """Verifies that the non-blocking bootstrap engine correctly initializes all services."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        """Build mock services and root."""
        # Access root from class variable to ensure it's available to instance methods
        self.mock_root = self.__class__.root
        self.mock_splash = MagicMock()
        self.mock_shutdown = MagicMock()
        
        self.mock_services = {
            "mqtt_conn": MagicMock(),
            "sub_router": MagicMock(),
            "state_cache": MagicMock(),
            "protocol_router": MagicMock(),
            "mirror_engine": MagicMock(),
            "splinker_manager": MagicMock()
        }
        
        self.mock_app_constants = MagicMock()
        self.mock_app_constants.global_settings = {"debug_enabled": False}
        
        self.engine = AsyncBootstrapEngine(
            self.mock_root, 
            self.mock_splash, 
            self.mock_services, 
            self.mock_app_constants, 
            self.mock_shutdown
        )

    def test_run_executes_phases(self):
        """OPERATE: Run engine. CHECK: Verify each initialization phase is triggered."""
        # Patch after to execute immediately for testing
        with patch.object(self.mock_root, 'after', side_effect=lambda delay, func: func()):
            with patch.object(self.engine, '_launch_app') as mock_launch:
                self.engine.run()
                
                # Phase 1: MQTT
                self.mock_services["mqtt_conn"].connect_to_broker.assert_called_once()
                
                # Phase 2: Protocols
                self.mock_services["protocol_router"].start.assert_called_once()
                
                # Phase 4: Splinker Control
                self.mock_services["sub_router"].subscribe_to_topic.assert_called()
                
                # Phase 5: Launch should be called
                mock_launch.assert_called_once()

    def test_failure_triggers_shutdown(self):
        """OPERATE: Trigger failure in bootstrap. CHECK: Verify shutdown is called."""
        # Configure mock to raise exception on connect_to_broker for this failure test
        self.mock_services["mqtt_conn"].connect_to_broker.side_effect = Exception("Boom")
        
        # Mock after to capture calls and execute them, then assert shutdown was called
        mock_after = MagicMock(side_effect=lambda delay, func: func())
        self.mock_root.after = mock_after
        
        self.engine.run()
        
        # Verify that on_closing was scheduled to be called
        mock_after.assert_called_with(0, self.mock_shutdown.on_closing)

if __name__ == '__main__':
    unittest.main()
