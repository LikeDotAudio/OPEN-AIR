# oaComProtocols.oaComMidi/Tests/test_midi.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.3
#
# Description: Unit tests for MidiManager ensuring Hub-and-Spoke integrity, 
# anti-feedback, and standardized standalone behavior.

import unittest
from unittest.mock import MagicMock, patch

# --- Target Module ---
from oaComProtocols.oaComMidi.Managers.midi_manager import MidiManager

class TestMidiManager(unittest.TestCase):
    """
    Architectural Integrity Tests for MIDI Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mocks and manager in isolation."""
        self.mock_state_cache = MagicMock()
        self.mock_router = MagicMock()
        
        # Patch ProtocolRouter to prevent real singleton access
        self.patcher_router = patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance", return_value=self.mock_router)
        self.patcher_router.start()
        
        # Build the manager
        self.midi = MidiManager(state_cache_manager=self.mock_state_cache, run_bridge=True, auto_start=False)
        
        # Inject mock components into the manager
        self.midi.ports = MagicMock()
        self.midi.mapper = MagicMock()
        self.midi.lock_manager = MagicMock()
        self.midi.lock_manager.is_locked.return_value = False
        
        # Set running state manually for deterministic test behavior
        self.midi._running = True

    def tearDown(self):
        """Cleanup patches."""
        self.midi.stop()
        self.patcher_router.stop()

    def test_spoke_to_hub_ingest(self):
        """OPERATE: Simulate incoming MIDI data (Spoke -> Hub)."""
        # BUILD
        test_port = MagicMock(); test_port.name = "TestPort"
        mock_message = MagicMock(); mock_message.type = "note_on"; mock_message.channel = 0; mock_message.note = 60; mock_message.velocity = 127
        test_port.iter_pending.return_value = [mock_message]
        
        self.midi.mapper.midi_to_topic.return_value = ("OPEN-AIR/MIDI/Note/60", 127)
        
        # OPERATE: Simulate one iteration of the listen loop
        self.midi._midi_listen_loop(test_port, _one_shot=True)
        
        # CHECK: Hub (StateCache) was updated with origin tagging
        self.mock_state_cache.handle_external_update.assert_called()
        args, kwargs = self.mock_state_cache.handle_external_update.call_args
        self.assertEqual(kwargs["metadata"]["origin_source"], "MIDI")

    def test_hub_to_spoke_dispatch(self):
        """OPERATE: Simulate Hub broadcast (Hub -> Spoke)."""
        # BUILD
        mock_out = MagicMock()
        mock_out.name = "TestOut"
        self.midi.ports.outports = [mock_out]
        self.midi.mapper.topic_to_midi.return_value = MagicMock() # Mocked MIDI message
        
        # OPERATE: Data from an external source (e.g., GUI)
        self.midi.publish("OPEN-AIR/MIDI/Note/60", {"value": 1.0}, {"origin_source": "GUI"})
        
        # CHECK: Transmitted to hardware Spoke
        self.midi.mapper.topic_to_midi.assert_called()
        mock_out.send.assert_called()

    def test_anti_feedback_echo_suppression(self):
        """CHECK: Verify messages originating from MIDI are NOT echoed back to MIDI."""
        # BUILD
        mock_out = MagicMock()
        mock_out.name = "TestOut"
        self.midi.ports.outports = [mock_out]
        
        # OPERATE: Data that originally came FROM MIDI
        self.midi.publish("OPEN-AIR/MIDI/Note/60", {"value": 0.5}, {"origin_source": "MIDI"})
        
        # CHECK: Echo suppression
        mock_out.send.assert_not_called()

    def test_telemetry_broadcast(self):
        """CHECK: Verify periodic status broadcast."""
        # BUILD
        mock_in = MagicMock(); mock_in.name = "TestIn"
        mock_out = MagicMock(); mock_out.name = "TestOut"
        self.midi.ports.inports = [mock_in]
        self.midi.ports.outports = [mock_out]
        
        # OPERATE
        self.midi._broadcast_status()
        
        # CHECK: Verify state cache notified
        calls = self.mock_state_cache.handle_external_update.call_args_list
        self.assertTrue(any("ActiveInputs" in c[0][0] for c in calls))

if __name__ == "__main__":
    unittest.main()
