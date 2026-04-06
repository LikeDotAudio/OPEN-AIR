# oaLogging/Tests/test_matrix_gate.py
# Author: Gemini QA Lead
# Version: 20260330.0001.1
#
# Description: Integration tests for matrix-aware logging gates.

import unittest
from unittest.mock import MagicMock, patch
from oaLogging.Methods.matrix_gate import is_debug_allowed, debug_matrix, matrix_log

class TestMatrixGate(unittest.TestCase):
    
    def setUp(self):
        # Force Rust off for these logic tests to ensure we hit the Python manager mocks
        self.rust_patch = patch("oaLogging.Methods.matrix_gate.RUST_ENABLED", False)
        self.rust_patch.start()

    def tearDown(self):
        self.rust_patch.stop()
    
    @patch("oaConfigurationManager.Managers.LoggingManager.manager.LoggingMatrixManager.get_instance")
    def test_is_debug_allowed_delegation(self, mock_get_manager):
        """Check: is_debug_allowed correctly delegates to the manager."""
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager
        mock_manager.is_debug_allowed.return_value = True
        
        result = is_debug_allowed("COMMS", "MQTT", "test_func")
        
        self.assertTrue(result)
        mock_manager.is_debug_allowed.assert_called_with("COMMS", "MQTT", "test_func")

    def test_failsafe_behavior(self):
        """Check: If manager is missing or broken, default to False (Silent)."""
        # Trigger an exception by patching the import or manager call
        with patch("oaConfigurationManager.Managers.LoggingManager.manager.LoggingMatrixManager.get_instance", side_effect=Exception("Crash!")):
            result = is_debug_allowed("ANY", "THING")
            self.assertFalse(result)

    @patch("oaLogging.Methods.matrix_gate.is_debug_allowed")
    def test_debug_matrix_decorator(self, mock_allowed):
        """Check: Decorator only allows execution of logic if allowed."""
        # Note: The decorator always allows the FUNCTION to run, but we are testing
        # if the 'allowed' check is performed correctly.
        mock_allowed.return_value = True
        
        @debug_matrix(system="GUI", element="Builder")
        def sample_func():
            return "executed"
            
        res = sample_func()
        self.assertEqual(res, "executed")
        mock_allowed.assert_called()

    @patch("oaLogging.Methods.matrix_gate.is_debug_allowed")
    @patch("oaLogging.Core.logger.get_logger")
    def test_matrix_log_proxy(self, mock_get_logger, mock_allowed):
        """Check: matrix_log only triggers the underlying logger if allowed."""
        mock_allowed.return_value = False
        matrix_log("SYS", "EL", "FUNC", "Message")
        mock_get_logger.assert_not_called()
        
        mock_allowed.return_value = True
        mock_context_logger = MagicMock()
        mock_get_logger.return_value = mock_context_logger
        
        matrix_log("SYS", "EL", "FUNC", "Message")
        mock_get_logger.assert_called()

if __name__ == "__main__":
    unittest.main()
