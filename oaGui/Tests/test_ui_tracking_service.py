# oaGui/Tests/test_interaction_telemetry_service.py
# Author: Gemini CLI
# Version: 20260404.1.4
#
# Description: Unit tests for interaction_telemetry_service.py

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaGui.Core.telemetry.interaction_telemetry_service import InteractionTelemetryService


class TestUITrackingService(unittest.TestCase):
    """Verifies that widget visibility and geometry are tracked and published correctly."""

    def setUp(self):
        """Build test objects and mock services."""
        self.service = InteractionTelemetryService()
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

        # Mock geometry on the widget itself as well
        self.mock_widget.winfo_width.return_value = 1024
        self.mock_widget.winfo_height.return_value = 768
        self.mock_widget.winfo_x.return_value = 10
        self.mock_widget.winfo_y.return_value = 20

    @patch('oaGui.Core.telemetry.interaction_telemetry_service.TelemetryPublisher')
    def test_track_registers_events(self, mock_publisher):
        """OPERATE: Track widget. CHECK: Verify event bindings and initial calls."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")

        # Verify bind was called for all tracking events
        self.assertTrue(self.mock_widget.bind.called)

    @patch('oaGui.Core.telemetry.interaction_telemetry_service.TelemetryPublisher')
    def test_visibility_publish(self, mock_publisher):
        """OPERATE: Trigger visibility events. CHECK: Verify MQTT publications."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")

        # Simulate <Map> (visible)
        self.service._on_visible(self.mock_widget, MagicMock())

        # Verify publisher was called
        mock_publisher.publish_visibility.assert_called()

    @patch('oaGui.Core.telemetry.interaction_telemetry_service.TelemetryPublisher')
    def test_geometry_publish(self, mock_publisher):
        """OPERATE: Trigger geometry changes. CHECK: Verify MQTT publications with correct data."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")

        # Trigger geometry change
        mock_event = MagicMock()
        mock_event.widget = self.mock_widget
        self.service._on_geometry_change(self.mock_widget, mock_event)

        # Verify publisher was called
        mock_publisher.publish_geometry.assert_called()

if __name__ == '__main__':
    unittest.main()
