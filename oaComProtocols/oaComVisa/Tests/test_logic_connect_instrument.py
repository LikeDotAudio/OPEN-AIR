# oaComProtocols.oaComVisa/Tests/test_logic_connect_instrument.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the VisaConnector class.

import unittest
from unittest.mock import MagicMock, patch
import pyvisa
import datetime

from oaComProtocols.oaComVisa.Workers.logic_connect_instrument import VisaConnector

class TestVisaConnector(unittest.TestCase):

    def setUp(self):
        """Set up the mock proxy and publisher and the VisaConnector instance."""
        self.mock_proxy = MagicMock()
        self.mock_publisher = MagicMock()
        self.connector = VisaConnector(visa_proxy=self.mock_proxy, gui_publisher=self.mock_publisher)

    @patch('oaComProtocols.oaComVisa.Workers.logic_connect_instrument.pyvisa.ResourceManager')
    def test_setup_visa_instrument_success(self, MockRM):
        """
        BUILD: Mock pyvisa.ResourceManager and open_resource.
        OPERATE: Call setup_visa_instrument.
        CHECK: Assert the instrument is returned and configured with correct parameters.
        """
        mock_rm = MockRM.return_value
        mock_inst = MagicMock()
        mock_rm.open_resource.return_value = mock_inst
        
        inst = self.connector.setup_visa_instrument("TCPIP::192.168.1.100::INSTR")
        
        self.assertEqual(inst, mock_inst)
        self.assertEqual(inst.timeout, 5000)
        self.assertEqual(inst.read_termination, "\n")
        self.assertEqual(inst.write_termination, "\n")
        self.assertEqual(inst.query_delay, 0.1)

    @patch('oaComProtocols.oaComVisa.Workers.logic_connect_instrument.pyvisa.ResourceManager')
    def test_setup_visa_instrument_failure(self, MockRM):
        """
        BUILD: Mock open_resource to raise an exception.
        OPERATE: Call setup_visa_instrument.
        CHECK: Assert it returns None on failure.
        """
        mock_rm = MockRM.return_value
        mock_rm.open_resource.side_effect = Exception("Connect error")
        
        inst = self.connector.setup_visa_instrument("TCPIP::invalid::INSTR")
        
        self.assertIsNone(inst)

    @patch.object(VisaConnector, 'setup_visa_instrument')
    def test_connect_instrument_logic_success(self, mock_setup):
        """
        BUILD: Mock setup_visa_instrument and the instrument's query response.
        OPERATE: Call connect_instrument_logic.
        CHECK: Assert it updates proxy, queries *IDN?, and publishes status updates.
        """
        mock_inst = MagicMock()
        mock_setup.return_value = mock_inst
        mock_inst.query.return_value = "TEKTRONIX,MSO2024B,SERIAL123,FV1.0"
        
        res = "TCPIP::1.2.3.4::INSTR"
        result = self.connector.connect_instrument_logic(res)
        
        self.assertEqual(result, mock_inst)
        self.mock_proxy.set_instrument_instance.assert_called_with(inst=mock_inst)
        mock_inst.query.assert_called_with("*IDN?")
        
        # Check some of the status publishes
        self.mock_publisher._publish_status.assert_any_call("brand", "TEKTRONIX")
        self.mock_publisher._publish_status.assert_any_call("device_model", "MSO2024B")
        self.mock_publisher._publish_status.assert_any_call("connected", True)

    @patch.object(VisaConnector, 'setup_visa_instrument')
    def test_connect_instrument_logic_setup_failure(self, mock_setup):
        """
        BUILD: Mock setup_visa_instrument to return None.
        OPERATE: Call connect_instrument_logic.
        CHECK: Assert it updates proxy with None and publishes failure status.
        """
        mock_setup.return_value = None
        
        result = self.connector.connect_instrument_logic("INVALID")
        
        self.assertFalse(result)
        self.mock_proxy.set_instrument_instance.assert_called_with(inst=None)
        self.mock_publisher._publish_status.assert_any_call("connected", False)
        self.mock_publisher._publish_status.assert_any_call("disconnected", True)

    @patch.object(VisaConnector, 'setup_visa_instrument')
    def test_connect_instrument_logic_query_failure(self, mock_setup):
        """
        BUILD: Mock instrument query to raise exception.
        OPERATE: Call connect_instrument_logic.
        CHECK: Assert it handles the exception and returns False.
        """
        mock_inst = MagicMock()
        mock_setup.return_value = mock_inst
        mock_inst.query.side_effect = Exception("Query timeout")
        
        result = self.connector.connect_instrument_logic("TCPIP::1.2.3.4::INSTR")
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
