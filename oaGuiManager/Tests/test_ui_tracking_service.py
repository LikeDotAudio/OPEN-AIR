# oaGuiManager/Tests/test_ui_tracking_service.py
# Author: Gemini CLI
# Version: 20260404.1.4
#
# Description: Unit tests for ui_tracking_service.py

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGuiManager.Core.telemetry.ui_tracking_service import UITrackingService


# Mocking is_connected as it's used by the module under test
# Patching it at the module level where it's imported by ui_tracking_service
@patch('oaGuiManager.Core.telemetry.ui_tracking_service.is_connected', return_value=True)
class TestUITrackingService(unittest.TestCase):
    """Verifies that widget visibility and geometry are tracked and published correctly."""

    def setUp(self):
        """Build test objects and mock services."""
        self.service = UITrackingService()
        self.mock_widget = MagicMock(spec=tk.Widget)
        self.mock_widget.winfo_exists.return_value = True

        # Use patch.object to mock methods on the mock_widget instance
        self.mock_widget.after = MagicMock(side_effect=lambda delay, func: func())
        self.mock_widget.after_cancel = MagicMock()

        self.mock_engine = MagicMock()
        self.mock_engine.base_topic = "OPEN-AIR"

        # Mock geometry for winfo_toplevel
        self.mock_toplevel = MagicMock()
        self.mock_toplevel.winfo_width.return_value = 1024
        self.mock_toplevel.winfo_height.return_value = 768
        self.mock_toplevel.winfo_x.return_value = 10
        self.mock_toplevel.winfo_y.return_value = 20
        self.mock_widget.winfo_toplevel.return_value = self.mock_toplevel

    def test_track_registers_events(self, mock_connected):
        """OPERATE: Track widget. CHECK: Verify event bindings and initial calls."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")

        # Verify bind was called for all tracking events
        self.assertTrue(self.mock_widget.bind.called)

    def test_visibility_publish(self, mock_connected):
        """OPERATE: Trigger visibility events. CHECK: Verify MQTT publications."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")

        # Simulate <Map> (visible)
        self.service._on_visible(self.mock_widget, MagicMock())

        # Verify any publish_command call happened
        self.assertTrue(self.mock_engine.publish_command.called)

        # Check topic of the last call for visibility
        # Looking for the last call in the list
        visibility_call = None
        for call in self.mock_engine.publish_command.call_args_list:
            if call[0][0] == "OPEN-AIR/panels/main/visibility/visible":
                visibility_call = call
                break
        self.assertIsNotNone(visibility_call, "Visibility publish topic not found")

    def test_geometry_publish(self, mock_connected):
        """OPERATE: Trigger geometry changes. CHECK: Verify MQTT publications with correct data."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")

        # Trigger geometry change
        self.service._on_geometry_change(self.mock_widget, MagicMock())

        # Verify geometry publication topic exists in the call list
        found = False
        for call in self.mock_engine.publish_command.call_args_list:
            if call[0][0] == "OPEN-AIR/panels/main/visibility/geometry":
                found = True
                break
        self.assertTrue(found, "Geometry publish topic not found")

if __name__ == '__main__':
    unittest.main()
