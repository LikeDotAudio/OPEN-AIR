# oaComProtocols.oaComVisa/Tests/test_logic_disconnect_instrument.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the VisaDisconnector class and disconnect_instrument function.

import unittest
from unittest.mock import MagicMock

from oaComProtocols.oaComVisa.Workers.logic_disconnect_instrument import VisaDisconnector, disconnect_instrument


class TestVisaDisconnector(unittest.TestCase):

    def setUp(self):
        """Set up the mock proxy and publisher and the VisaDisconnector instance."""
        self.mock_proxy = MagicMock()
        self.mock_publisher = MagicMock()
        self.disconnector = VisaDisconnector(visa_proxy=self.mock_proxy, gui_publisher=self.mock_publisher)

    def test_disconnect_instrument_success(self):
        """Test the standalone disconnect_instrument function with a valid instrument."""
        mock_inst = MagicMock()
        result = disconnect_instrument(mock_inst)

        self.assertTrue(result)
        mock_inst.close.assert_called_once()

    def test_disconnect_instrument_failure(self):
        """Test the standalone disconnect_instrument function when close raises an exception."""
        mock_inst = MagicMock()
        mock_inst.close.side_effect = Exception("Close error")
        result = disconnect_instrument(mock_inst)

        self.assertFalse(result)

    def test_disconnect_instrument_none(self):
        """Test the standalone disconnect_instrument function with None."""
        result = disconnect_instrument(None)
        self.assertFalse(result)

    def test_disconnect_instrument_logic_with_inst(self):
        """
        BUILD: Mock a valid instrument.
        OPERATE: Call disconnect_instrument_logic.
        CHECK: Assert it closes the instrument, resets the proxy, and publishes status updates.
        """
        mock_inst = MagicMock()

        result = self.disconnector.disconnect_instrument_logic(mock_inst)

        self.assertTrue(result)
        mock_inst.close.assert_called_once()
        self.mock_proxy.set_instrument_instance.assert_called_with(inst=None)
        self.mock_publisher._publish_status.assert_any_call("brand", "N/A")
        self.mock_publisher._publish_proxy_status.assert_called_with("DISCONNECTED")

    def test_disconnect_instrument_logic_no_inst(self):
        """
        BUILD: No instrument (None).
        OPERATE: Call disconnect_instrument_logic.
        CHECK: Assert it resets the proxy and publishes disconnected status.
        """
        result = self.disconnector.disconnect_instrument_logic(None)

        self.assertTrue(result)
        self.mock_proxy.set_instrument_instance.assert_called_with(inst=None)
        self.mock_publisher._publish_proxy_status.assert_called_with("DISCONNECTED")

if __name__ == '__main__':
    unittest.main()
