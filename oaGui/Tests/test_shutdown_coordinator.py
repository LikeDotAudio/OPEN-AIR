# oaGui/Tests/test_shutdown_coordinator.py
# Author: Gemini CLI
# Version: 20260409.1.1
#
# Description: Unit tests for shutdown_coordinator.py (Optimized for synchronous execution)

import tkinter as tk
import unittest
from unittest.mock import MagicMock

from oaGui.Core.shutdown_coordinator import ShutdownCoordinator


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
        """OPERATE: Trigger on_closing synchronously. CHECK: Verify managers are signaled to stop."""
        # Use run_async=False to execute logic in the current thread
        self.coordinator.on_closing(run_async=False)

        # Verify stop/shutdown/disconnect was called on instances
        # (It checks for .stop() first in ShutdownCoordinator)
        self.mock_service1.stop.assert_called_once()
        self.mock_service2.stop.assert_called_once()

        # Verify root.quit was scheduled
        self.mock_root.after.assert_called_with(0, self.mock_root.quit)

    def test_on_closing_multiple_calls(self):
        """OPERATE: Trigger on_closing twice. CHECK: Ensure logic only runs once."""
        # Use run_async=False to avoid debugger thread artifacts
        self.coordinator.on_closing(run_async=False)
        self.coordinator.on_closing(run_async=False)

        # Managers should only be stopped once even if on_closing is triggered multiple times
        self.mock_service1.stop.assert_called_once()

    def test_attach_to_root(self):
        """OPERATE: Attach to root. CHECK: Verify protocol is set."""
        self.coordinator.attach_to_root()
        self.mock_root.protocol.assert_called_with("WM_DELETE_WINDOW", self.coordinator.on_closing)

if __name__ == '__main__':
    unittest.main()
