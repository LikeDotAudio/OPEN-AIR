# oaComProtocols.oaComMidi/Tests/test_midi_tx.py
#
# Unit tests for the MIDI Transmission (TX) logic.
#
# Author: Anthony Peter Kuzub
# Version: 20260401.1000.1

import unittest
from unittest.mock import MagicMock, patch
from oaComProtocols.oaComMidi.Managers.midi_manager import MidiManager

class TestMidiTx(unittest.TestCase):
    def setUp(self):
        self.state_cache = MagicMock()
        # Mock ProtocolRouter to avoid actual network/threading
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
            self.midi = MidiManager(self.state_cache, run_bridge=True)
            self.midi._running = True

    def tearDown(self):
        if hasattr(self, 'midi'):
            self.midi.stop()

    def test_publish_cc_to_midi(self):
        """Test that a system CC topic is correctly translated and sent to MIDI ports."""
        mock_out = MagicMock()
        mock_out.name = "MockPort"
        self.midi.ports.outports = [mock_out]
        
        topic = "OPEN-AIR/MIDI/my_device/ch0/cc7"
        val = {"val": 127}
        
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
            self.midi.publish(topic, val)
        
        # Verify mido.Message was sent
        self.assertTrue(mock_out.send.called)
        msg = mock_out.send.call_args[0][0]
        self.assertEqual(msg.type, 'control_change')
        self.assertEqual(msg.channel, 0)
        self.assertEqual(msg.control, 7)
        self.assertEqual(msg.value, 127)

    def test_publish_note_to_midi(self):
        """Test that a system Note topic is correctly translated and sent to MIDI ports."""
        mock_out = MagicMock()
        mock_out.name = "MockPort"
        self.midi.ports.outports = [mock_out]
        
        topic = "OPEN-AIR/MIDI/my_device/ch2/note60"
        val = 100
        
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
            self.midi.publish(topic, val)
        
        # Verify mido.Message was sent
        self.assertTrue(mock_out.send.called)
        msg = mock_out.send.call_args[0][0]
        self.assertEqual(msg.type, 'note_on')
        self.assertEqual(msg.channel, 2)
        self.assertEqual(msg.note, 60)
        self.assertEqual(msg.velocity, 100)

if __name__ == "__main__":
    unittest.main()
