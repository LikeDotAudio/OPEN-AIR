import unittest
from unittest.mock import MagicMock, patch
from workers.Command_Router.MIDI.midi import MidiManager

class TestMidiManager(unittest.TestCase):
    def setUp(self):
        self.state_cache = MagicMock()
        with patch("workers.Command_Router.protocol_router.ProtocolRouter.get_instance"):
            self.midi = MidiManager(self.state_cache, run_bridge=True)

    def test_status_broadcast(self):
        """Goal: Verify that starting the MIDI manager broadcasts active ports to the system state."""
        # Setup mock ports
        mock_in = MagicMock(); mock_in.name = "TestIn"
        mock_out = MagicMock(); mock_out.name = "TestOut"
        self.midi.ports.inports = [mock_in]
        self.midi.ports.outports = [mock_out]
        
        # Trigger broadcast
        self.midi._broadcast_status()
        
        # CHECK: State cache notified of inputs and outputs
        calls = self.state_cache.handle_external_update.call_args_list
        self.assertTrue(any("ActiveInputs" in c[0][0] for c in calls))
        self.assertTrue(any("ActiveOutputs" in c[0][0] for c in calls))

if __name__ == "__main__":
    unittest.main()
