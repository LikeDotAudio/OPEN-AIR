# oaComMidi/Tests/test_midi.py
#
# Unit tests for the modular MIDI Orchestrator.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1400.1

import unittest
from unittest.mock import MagicMock, patch
from oaComMidi.Entry import MidiManager

class TestMidiManager(unittest.TestCase):
    """
    Validation suite for the MidiManager orchestrator.
    
    This suite verifies that the MidiManager correctly interacts with the 
    global state cache, protocol router, and virtual MIDI ports.
    """
    def setUp(self):
        """
        Initializes a mock environment for each test case.
        
        Side Effects:
            - Allocates a MagicMock for the state cache.
            - Patches the ProtocolRouter singleton.
            - Instantiates a MidiManager in bridge mode.
        """
        self.state_cache = MagicMock()
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance"):
            self.midi = MidiManager(self.state_cache, run_bridge=True)

    def test_status_broadcast(self):
        """
        Goal: Verify that starting the MIDI manager broadcasts active ports to 
        the system state.
        
        Verification:
            - Confirms that handle_external_update is called for both 
              Inputs and Outputs.
        """
        # Setup mock ports with valid names.
        mock_in = MagicMock(); mock_in.name = "TestIn"
        mock_out = MagicMock(); mock_out.name = "TestOut"
        self.midi.ports.inports = [mock_in]
        self.midi.ports.outports = [mock_out]
        
        # Trigger the status broadcast sequence.
        self.midi._broadcast_status()
        
        # Validation: Verify that the state cache was notified of the port changes.
        calls = self.state_cache.handle_external_update.call_args_list
        self.assertTrue(any("ActiveInputs" in c[0][0] for c in calls))
        self.assertTrue(any("ActiveOutputs" in c[0][0] for c in calls))

if __name__ == "__main__":
    unittest.main()
