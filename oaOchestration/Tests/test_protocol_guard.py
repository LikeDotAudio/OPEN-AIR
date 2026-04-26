# oaOchestration/Tests/test_protocol_guard.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the protocol_guard decorator.

import unittest
from unittest.mock import patch

from oaOchestration.Managers.protocol_guard import protocol_guard


class TestProtocolGuard(unittest.TestCase):

    @patch('oaOchestration.Managers.protocol_guard.router_logger')
    def test_protocol_guard_success(self, mock_logger):
        """
        BUILD: Create a mock function decorated with protocol_guard.
        OPERATE: Call the function normally.
        CHECK: Assert the function returns its expected result and no errors are logged.
        """
        @protocol_guard("TEST_PROTOCOL")
        def successful_func(x, y):
            return x + y

        result = successful_func(2, 3)

        self.assertEqual(result, 5)
        mock_logger.error.assert_not_called()

    @patch('oaOchestration.Managers.protocol_guard.router_logger')
    def test_protocol_guard_exception(self, mock_logger):
        """
        BUILD: Create a mock function decorated with protocol_guard that raises an Exception.
        OPERATE: Call the function.
        CHECK: Assert the exception is caught, an error is logged with the protocol name, and None is returned.
        """
        @protocol_guard("TEST_PROTOCOL")
        def failing_func():
            raise ValueError("Something went wrong")

        result = failing_func()

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        args, _ = mock_logger.error.call_args
        self.assertIn("TEST_PROTOCOL", args[0])
        self.assertIn("Something went wrong", args[0])
        self.assertIn("Dispatch Failure", args[0])

if __name__ == '__main__':
    unittest.main()
