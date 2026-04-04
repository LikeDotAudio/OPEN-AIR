# oaGuiManager/Tests/test_shutdown_coordinator.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for shutdown_coordinator.py

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaGuiManager.Core.shutdown_coordinator import ShutdownCoordinator

class TestShutdownCoordinator(unittest.TestCase):
    """Verifies that the shutdown coordinator correctly stops all services."""

    def setUp(self):
        """Build test objects and mock services."""
        self.mock_root = MagicMock(spec=tk.Tk)
        self.mock_root.after = MagicMock(side_effect=lambda delay, func: func()) # Execute after-calls immediately
        
        self.mock_service1 = MagicMock()
        self.mock_service2 = MagicMock()
        
        self.shared_instances = {
            "service1": self.mock_service1,
            "service2": self.mock_service2
        }
        
        self.coordinator = ShutdownCoordinator(self.mock_root, self.shared_instances)

    def test_on_closing_stops_managers(self):
        """OPERATE: Trigger on_closing. CHECK: Verify managers are signaled to stop."""
        with patch('threading.Thread') as mock_thread:
            # We mock threading to control execution
            self.coordinator.on_closing()
            
            # Verify a thread was started to handle manager stops
            mock_thread.assert_called_once()
            
            # Manually run the target function of the thread
            target_fn = mock_thread.call_args[1]['target']
            target_fn()
            
            # Verify stop/shutdown/disconnect was called on instances
            self.mock_service1.stop.assert_called_once()
            self.mock_service2.stop.assert_called_once()
            
            # Verify root.quit was scheduled
            self.mock_root.after.assert_called_with(0, self.mock_root.quit)

    def test_on_closing_multiple_calls(self):
        """OPERATE: Trigger on_closing twice. CHECK: Ensure it only runs once."""
        with patch('threading.Thread') as mock_thread:
            self.coordinator.on_closing()
            self.coordinator.on_closing()
            
            # Thread should only be started once
            mock_thread.assert_called_once()

    def test_attach_to_root(self):
        """OPERATE: Attach to root. CHECK: Verify protocol is set."""
        self.coordinator.attach_to_root()
        self.mock_root.protocol.assert_called_with("WM_DELETE_WINDOW", self.coordinator.on_closing)

if __name__ == '__main__':
    unittest.main()
