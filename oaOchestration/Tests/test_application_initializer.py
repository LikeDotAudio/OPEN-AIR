# oaOchestration/Tests/test_application_initializer.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the application_initializer.py functions.

import unittest
from unittest.mock import patch, MagicMock

from oaOchestration.Managers.application_initializer import initialize_app

class TestApplicationInitializer(unittest.TestCase):

    @patch('oaOchestration.Managers.application_initializer.logger')
    def test_initialize_app_success(self, mock_logger):
        """
        BUILD: Mock the logger to capture log calls.
        OPERATE: Call initialize_app().
        CHECK: Assert it returns True and logs the success message.
        """
        # Set LOCAL_DEBUG to True in the module so logger calls are hit
        with patch('oaOchestration.Managers.application_initializer.LOCAL_DEBUG', True):
            result = initialize_app()
            
            self.assertTrue(result)
            mock_logger.debug.assert_called()
            mock_logger.success.assert_called_with("🚀🏗️✅ [SUCCESS] Application initialization completed.")

    @patch('oaOchestration.Managers.application_initializer.logger')
    def test_initialize_app_exception(self, mock_logger):
        """
        BUILD: Mock the logger and force an exception during initialization.
        OPERATE: Call initialize_app().
        CHECK: Assert it handles the exception, logs the error, and returns False.
        """
        # Force an exception by mocking something inside the function 
        # or in this case, since it does almost nothing, we'll patch logger.success to raise Exception
        mock_logger.success.side_effect = Exception("Forced error")
        
        with patch('oaOchestration.Managers.application_initializer.LOCAL_DEBUG', True):
            result = initialize_app()
            
            self.assertFalse(result)
            mock_logger.exception.assert_called()
            args, _ = mock_logger.exception.call_args
            self.assertIn("Error during application initialization: Forced error", args[0])

if __name__ == '__main__':
    unittest.main()
