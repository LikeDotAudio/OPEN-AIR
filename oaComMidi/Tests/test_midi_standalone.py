# oaComMidi/Tests/test_midi_standalone.py
#
# Unit tests for MIDI Standalone operation (No MQTT).
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import unittest
from unittest.mock import MagicMock, patch
from oaComMidi.Managers.midi_manager import MidiManager

class TestMidiStandalone(unittest.TestCase):
    def setUp(self):
        # Initialize without state manager (Standalone)
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
            self.midi = MidiManager(state_cache_manager=None, run_bridge=True)
            self.midi._running = True

    def test_monitor_notification_no_mqtt(self):
        """Test that local monitors are notified even if MQTT is not available."""
        monitor_cb = MagicMock()
        self.midi.add_monitor_callback(monitor_cb)
        
        # Simulate a fake port and message
        mock_port = MagicMock()
        mock_port.name = "StandalonePort"
        
        import mido
        msg = mido.Message('control_change', channel=0, control=7, value=64)
        mock_port.iter_pending.return_value = [msg]
        
        # Manually trigger one iteration of the loop logic
        # We patch time.sleep to avoid waiting
        # We need to make it exit after one iteration
        def side_effect():
            # First call returns our message
            yield [msg]
            # Then we stop the loop
            self.midi._running = False
            # Second call returns empty to let the loop proceed to check the flag
            yield []

        mock_port.iter_pending.side_effect = side_effect()

        # Manually trigger one iteration of the loop logic
        with patch("time.sleep"):
            self.midi._midi_listen_loop(mock_port)
            
        # Verify monitor was notified
        self.assertTrue(monitor_cb.called)
        direction, received_msg = monitor_cb.call_args[0]
        self.assertEqual(direction, "RX")
        self.assertEqual(received_msg, msg)

if __name__ == "__main__":
    unittest.main()
