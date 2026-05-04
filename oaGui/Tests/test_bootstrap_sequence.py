# oaGui/Tests/test_loader_bootstrap_engine.py
# Author: Gemini CLI
# Version: 20260404.1.6
#
# Description: Unit tests for loader_bootstrap_engine.py

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGui.Managers.bootstrap.loader_bootstrap_engine import LoaderBootstrapEngine


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

        self.engine = LoaderBootstrapEngine(
            self.mock_root,
            self.mock_splash,
            self.mock_services,
            self.mock_app_constants,
            self.mock_shutdown
        )

    @patch('oaGui.Managers.bootstrap.loader_bootstrap_engine.launch_workspace_application')
    @patch('oaGui.Managers.bootstrap.loader_bootstrap_engine.assemble_system_control_links')
    @patch('oaGui.Managers.bootstrap.loader_bootstrap_engine.ignite_protocol_services')
    @patch('oaGui.Managers.bootstrap.loader_bootstrap_engine.initialize_communications')
    def test_run_executes_phases(self, mock_init, mock_ignite, mock_assemble, mock_launch):
        """OPERATE: Run engine. CHECK: Verify each initialization phase is triggered."""
        # Patch after to execute immediately for testing
        with patch.object(self.mock_root, 'after', side_effect=lambda delay, func: func()):
            self.engine.run()

            # Phase 1: Communication
            mock_init.assert_called_once()

            # Phase 2: Protocols
            mock_ignite.assert_called_once()

            # Phase 4: Splinker Control
            mock_assemble.assert_called_once()

            # Phase 5: Launch should be called
            mock_launch.assert_called_once()

    @patch('oaLogging.Methods.matrix_gate.is_debug_allowed', return_value=False)
    @patch('oaGui.Managers.bootstrap.loader_bootstrap_engine.logger')
    def test_failure_triggers_shutdown(self, mock_logger, mock_is_debug_allowed):
        """OPERATE: Trigger failure in bootstrap. CHECK: Verify shutdown is called."""
        # Patch init to raise exception
        with patch('oaGui.Managers.bootstrap.loader_bootstrap_engine.initialize_communications', side_effect=Exception("Boom")):
            # Mock after to capture calls and execute them, then assert shutdown was called
            mock_after = MagicMock(side_effect=lambda delay, func: func())
            self.mock_root.after = mock_after

            self.engine.run()
            
            # Verify the error was logged
            mock_logger.error.assert_called()

            # Verify that on_closing was scheduled to be called
            mock_after.assert_any_call(0, self.mock_shutdown.on_closing)

if __name__ == '__main__':
    unittest.main()
