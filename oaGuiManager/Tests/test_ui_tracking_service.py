# oaGuiManager/Tests/test_ui_tracking_service.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for ui_tracking_service.py

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import time
from oaGuiManager.Core.telemetry.ui_tracking_service import UITrackingService

class TestUITrackingService(unittest.TestCase):
    """Verifies that widget visibility and geometry are tracked and published correctly."""

    def setUp(self):
        """Build test objects and mock services."""
        self.service = UITrackingService()
        self.mock_widget = MagicMock(spec=tk.Widget)
        self.mock_widget.winfo_exists.return_value = True
        self.mock_widget.after = MagicMock(side_effect=lambda delay, func: func()) # Instant debouncing
        
        self.mock_engine = MagicMock()
        self.mock_engine.base_topic = "OPEN-AIR"
        
        # Mock geometry for winfo_toplevel
        self.mock_toplevel = MagicMock()
        self.mock_toplevel.winfo_width.return_value = 1024
        self.mock_toplevel.winfo_height.return_value = 768
        self.mock_toplevel.winfo_x.return_value = 10
        self.mock_toplevel.winfo_y.return_value = 20
        self.mock_widget.winfo_toplevel.return_value = self.mock_toplevel

    @patch('oaComMQTT.Core.mqtt_publisher_service.is_connected', return_value=True)
    def test_track_registers_events(self, mock_connected):
        """OPERATE: Track widget. CHECK: Verify event bindings and initial calls."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")
        
        # Verify bind was called for all tracking events
        self.mock_widget.bind.assert_any_call("<Map>", unittest.mock.ANY, add="+")
        self.mock_widget.bind.assert_any_call("<Unmap>", unittest.mock.ANY, add="+")
        self.mock_widget.bind.assert_any_call("<Configure>", unittest.mock.ANY, add="+")

    @patch('oaComMQTT.Core.mqtt_publisher_service.is_connected', return_value=True)
    def test_visibility_publish(self, mock_connected):
        """OPERATE: Trigger visibility events. CHECK: Verify MQTT publications."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")
        
        # Simulate <Map> (visible)
        self.service._on_visible(self.mock_widget, MagicMock())
        self.mock_engine.publish_command.assert_any_call(
            "OPEN-AIR/panels/main/visibility/visible", 
            unittest.mock.ANY
        )
        # Ensure it contains 'visible': true
        payload = self.mock_engine.publish_command.call_args_list[-2][0][1]
        self.assertIn('"visible":true', payload)

        # Simulate <Unmap> (hidden)
        self.service._on_hidden(self.mock_widget, MagicMock())
        payload = self.mock_engine.publish_command.call_args_list[-1][0][1]
        self.assertIn('"visible":false', payload)

    @patch('oaComMQTT.Core.mqtt_publisher_service.is_connected', return_value=True)
    def test_geometry_publish(self, mock_connected):
        """OPERATE: Trigger geometry changes. CHECK: Verify MQTT publications with correct data."""
        self.service.track(self.mock_widget, "MainTab", self.mock_engine, "panels/main")
        
        # Simulate <Configure>
        self.service._on_geometry_change(self.mock_widget, MagicMock())
        
        # Verify geometry publication
        self.mock_engine.publish_command.assert_any_call(
            "OPEN-AIR/panels/main/visibility/geometry", 
            unittest.mock.ANY
        )
        payload = self.mock_engine.publish_command.call_args_list[-1][0][1]
        self.assertIn('"width":1024', payload)
        self.assertIn('"height":768', payload)
        self.assertIn('"x":10', payload)
        self.assertIn('"y":20', payload)

if __name__ == '__main__':
    unittest.main()
