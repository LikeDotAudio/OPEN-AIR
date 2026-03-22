# Tests/test_state_mirror_engine.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from oaTranslator.Core.state_mirror_engine import StateMirrorEngine

class TestStateMirrorEngine(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except:
            self.root = MagicMock()
        self.base_topic = "OPEN-AIR"
        self.subscriber_router = MagicMock()
        self.state_cache_manager = MagicMock()
        self.engine = StateMirrorEngine(
            self.base_topic, 
            self.subscriber_router, 
            self.root, 
            self.state_cache_manager
        )

    def tearDown(self):
        self.root.destroy()

    def test_calculate_topic(self):
        """Test topic calculation logic."""
        topic = self.engine.calculate_topic("volume", "MainTab")
        self.assertEqual(topic, "OPEN-AIR/MainTab/volume")

    def test_register_widget(self):
        """Test widget registration and topic binding."""
        var = tk.DoubleVar(value=10.0, master=self.root)
        config = {"dynamics": {"path": "custom/path"}}
        topic = self.engine.register_widget("widget1", var, "Tab1", config)
        
        self.assertEqual(topic, "OPEN-AIR/Tab1/custom/path")
        self.assertIn("widget1", self.engine.registered_widgets)

    @patch("oaComMQTT.Core.mqtt_publisher_service.publish_payload")
    def test_broadcast_gui_change(self, mock_publish):
        """Test that GUI changes trigger MQTT publication."""
        var = tk.DoubleVar(value=10.0, master=self.root)
        config = {}
        self.engine.register_widget("widget1", var, "Tab1", config)
        
        # Simulate value change
        var.set(20.0)
        
        # We need to manually call broadcast or wait for trace
        # Trace is asynchronous or handled by tk event loop
        self.engine.broadcast_gui_change_to_mqtt("widget1")
        
        # Verify publish_payload was called
        # Note: if state_cache_manager is provided, it calls that instead
        if self.state_cache_manager:
            self.state_cache_manager.handle_external_update.assert_called()
        else:
            mock_publish.assert_called()

if __name__ == "__main__":
    unittest.main()
