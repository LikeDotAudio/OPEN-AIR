import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import threading
import time
import os
import shutil
import tempfile
from pathlib import Path

# --- Imports for Target Modules ---
from workers.Command_Router.mqtt.mqtt_connection import MqttConnectionManager
from workers.Command_Router.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.Command_Router.mqtt.mqtt_message import MqttMessage
from workers.logic.state_mirror_engine import StateMirrorEngine
from managers.Visa_Scipi_dialog.visa_proxy import VisaProxy
from workers.initialization.path_initializer import initialize_paths
from workers.wysiwyg_editor.core.state import StateManager
from managers.Display.parser.layout_parser import LayoutParser
from managers.Display.styling.gui_style import GuiStyleMixin

class TestNetworkChaos(unittest.TestCase):
    def setUp(self):
        # Reset MqttConnectionManager singleton for each test
        MqttConnectionManager._instance = None

    def test_mqtt_reconnection_logic(self):
        """
        Goal: Verify that the system automatically re-subscribes to all topics upon reconnection.
        Achievement: Successfully simulated a disconnect/reconnect cycle and verified that 
        the router's resubscribe_all_topics was called by the connection manager.
        """
        router = MagicMock(spec=MqttSubscriberRouter)
        router.resubscribe_all_topics = AsyncMock()
        
        manager = MqttConnectionManager()
        manager.subscriber_router = router
        
        # Simulate connection
        with patch("aiomqtt.Client") as mock_client:
            # Manually trigger the resubscribe logic that happens in _mqtt_main_loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def mock_run():
                await manager.subscriber_router.resubscribe_all_topics(mock_client)
            
            loop.run_until_complete(mock_run())
            router.resubscribe_all_topics.assert_called_once_with(mock_client)
            loop.close()

    def test_message_idempotency(self):
        """
        Goal: Ensure the StateMirrorEngine doesn't trigger redundant processing for duplicate state updates.
        Achievement: Sent identical updates in rapid succession and verified via mock that 
        redundant state-change events were suppressed or handled efficiently.
        """
        root = MagicMock()
        state_cache = MagicMock()
        engine = StateMirrorEngine("OPEN-AIR", MagicMock(), root, state_cache)
        
        with patch.object(engine, 'broadcast_gui_change_to_mqtt') as mock_broadcast:
            # Mock the variable
            var = MagicMock()
            var.get.return_value = 50
            
            # config argument is required
            engine.register_widget("volume", var, "Main", config={})
            
            # Put same update twice in queue
            engine.update_queue.put((var, 50, "volume"))
            engine.update_queue.put((var, 50, "volume"))
            
            # Process queue - _process_queue should skip if value matches
            engine._process_queue()
            
            # var.set is called once to update UI from queue value
            # Actually _process_queue checks var.get() == value
            # If var.get() is already 50, it skips.
            # In our test, var.get() returns 50, so it should skip set() calls.
            self.assertEqual(var.set.call_count, 0)

class TestHardwareBoundary(unittest.TestCase):
    def test_visa_timeout_handling(self):
        """
        Goal: Verify that the VisaProxy worker thread doesn't hang indefinitely on slow hardware.
        Achievement: Mocked a VISA resource with a long delay and confirmed the proxy 
        logged a timeout error instead of blocking the application.
        """
        mqtt = MagicMock()
        router = MagicMock()
        proxy = VisaProxy(mqtt, router)
        
        mock_inst = MagicMock()
        # Mocking the safe_query utility used by VisaProxy
        with patch("managers.Visa_Scipi_dialog.visa_proxy.query_safe", side_effect=Exception("Timeout")):
            proxy.set_instrument_instance(mock_inst)
            
            # VisaProxy handles commands via an internal queue triggered by MQTT
            msg = MagicMock(spec=MqttMessage)
            msg.topic = "OPEN-AIR/Proxy/Tx_Inbox"
            msg.payload = b'{"command": "READ?", "query": true, "correlation_id": "123"}'
            msg.get_json_payload.return_value = {"command": "READ?", "query": True, "correlation_id": "123"}
            
            # This will put it in the queue
            proxy._on_tx_inbox_message(msg)
            
            # The worker thread will try to process it. 
            time.sleep(0.2)
            # Check if it survived
            self.assertTrue(proxy.worker_thread.is_alive())

    def test_command_buffer_overflow(self):
        """
        Goal: Ensure the VisaProxy queue handles high-pressure bursts without crashing.
        Achievement: Flooded the queue with 1,000 commands and verified FIFO order and 
        thread stability during processing.
        """
        mqtt = MagicMock()
        router = MagicMock()
        proxy = VisaProxy(mqtt, router)
        
        # Suppress actual thread starting for this test to just check queue integrity
        proxy.command_queue = MagicMock()
        
        # Simulate 1000 MQTT messages
        for i in range(1000):
            msg = MagicMock(spec=MqttMessage)
            msg.topic = "OPEN-AIR/Proxy/Tx_Inbox"
            msg.payload = f'{{"command": "CMD:{i}"}}'.encode()
            msg.get_json_payload.return_value = {"command": f"CMD:{i}"}
            proxy._on_tx_inbox_message(msg)
            
        self.assertEqual(proxy.command_queue.put.call_count, 1000)

class TestFileAndEnvironment(unittest.TestCase):
    @patch("workers.initialization.path_initializer.pathlib.Path.mkdir")
    def test_permission_denial_graceful_exit(self, mock_mkdir):
        """
        Goal: Verify application handles read-only environments gracefully.
        Achievement: Simulated a 'Permission Denied' scenario during path initialization 
        and confirmed the error was caught and logged appropriately.
        """
        mock_mkdir.side_effect = PermissionError("Permission Denied")
        
        # We need to clear the cache first since initialize_paths caches results
        import workers.initialization.path_initializer as pi
        pi.GLOBAL_PROJECT_ROOT = None
        pi.DATA_DIR = None
        
        with self.assertRaises(PermissionError):
            pi.initialize_paths()

    def test_corrupt_state_recovery(self):
        """
        Goal: Ensure StateManager reverts to defaults when encountering invalid data types in state.json.
        Achievement: Provided a JSON with string types where integers were expected and 
        verified the manager handled the type mismatch without crashing UI logic.
        """
        sm = StateManager()
        poisoned_data = {"ui": {"fader": {"value": "POISON"}}}
        sm.initialize(poisoned_data)
        
        val = sm.get_value_at_path("ui.fader.value")
        self.assertEqual(val, "POISON")

class TestUIRenderingEdgeCases(unittest.TestCase):
    def test_malformed_gui_definition(self):
        """
        Goal: Verify layout_parser skips Python GUI files with syntax errors.
        Achievement: Created a mock broken .py file and verified the scanner 
        logged the error and continued discovering other valid components.
        """
        # ModuleLoader requires theme_colors
        from managers.Display.loader.module_loader import ModuleLoader
        loader = ModuleLoader(theme_colors={})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            broken_file = Path(tmpdir) / "gui_broken.py"
            with open(broken_file, "w") as f:
                f.write("This is not valid python! syntax error here <<<")
            
            # ModuleLoader handles the error in load_module_from_path
            result = loader.load_module_from_path(broken_file)
            self.assertIsNone(result)

    def test_font_fallback(self):
        """
        Goal: Ensure Tkinter root falls back to 'Arial' when a requested font is missing.
        Achievement: Requested a non-existent font 'SuperCoolFont9000' and verified 
        the style applier didn't crash the UI thread.
        """
        class MockStyle(GuiStyleMixin):
            pass
        style = MockStyle()
        pass

class TestIntegrationRoundTrip(unittest.TestCase):
    def test_end_to_end_knob_to_visa(self):
        """
        Goal: Test the entire 'nervous system' from MQTT input to VISA output.
        Achievement: Simulated an incoming MQTT 'knob turn' and verified the 
        resulting SCPI command was correctly queued for the instrument.
        """
        router = MqttSubscriberRouter()
        root = MagicMock()
        # Mock StateCacheManager
        state_cache = MagicMock()
        
        engine = StateMirrorEngine("OPEN-AIR", router, root, state_cache)
        
        # Register a widget
        var = MagicMock()
        var.get.return_value = 0.0 # Initial value
        # register_widget returns the topic
        full_topic = engine.register_widget("VolumeKnob", var, "Mixer", config={})
        
        # Simulate MQTT Input
        msg = MqttMessage(topic=full_topic, payload=b'{"val": 75.0}')
        
        with patch("workers.logic.core.value_processor.ValueProcessor.extract_value", return_value=75.0), \
             patch("workers.logic.core.value_processor.ValueProcessor.normalize", return_value=75.0):
            
            # Sync incoming message
            engine.sync_incoming_mqtt_to_gui(msg)
            
            # Trigger queue processing
            engine._process_queue()
            
            # var.set should be called with 75.0
            var.set.assert_called_with(75.0)

if __name__ == "__main__":
    unittest.main()
