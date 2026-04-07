# oaComProtocols.oaComVisa/Tests/test_agent_usb_enumerator.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the discover_usb_devices function.

import unittest
from unittest.mock import MagicMock

from oaComProtocols.oaComVisa.Workers.agent_usb_enumerator import discover_usb_devices

class TestAgentUsbEnumerator(unittest.TestCase):

    def test_discover_usb_devices_success(self):
        """
        BUILD: Mock RM with a mix of USB, TCPIP, and ASRL resources.
        OPERATE: Call discover_usb_devices.
        CHECK: Assert only USB resources are returned.
        """
        mock_rm = MagicMock()
        mock_rm.list_resources.return_value = (
            "USB0::0x1234::0x5678::SERIAL::0::INSTR",
            "TCPIP0::192.168.1.100::INSTR",
            "ASRL1::INSTR",
            "USB0::0xAAAA::0xBBBB::SERIAL::0::INSTR"
        )
        
        devices = discover_usb_devices(mock_rm)
        
        self.assertEqual(len(devices), 2)
        self.assertIn("USB0::0x1234::0x5678::SERIAL::0::INSTR", devices)
        self.assertIn("USB0::0xAAAA::0xBBBB::SERIAL::0::INSTR", devices)
        self.assertNotIn("TCPIP0::192.168.1.100::INSTR", devices)
        self.assertNotIn("ASRL1::INSTR", devices)

    def test_discover_usb_devices_empty(self):
        """
        BUILD: Mock RM with no resources.
        OPERATE: Call discover_usb_devices.
        CHECK: Assert an empty list is returned.
        """
        mock_rm = MagicMock()
        mock_rm.list_resources.return_value = ()
        
        devices = discover_usb_devices(mock_rm)
        self.assertEqual(devices, [])

    def test_discover_usb_devices_exception(self):
        """
        BUILD: Mock RM to raise an exception.
        OPERATE: Call discover_usb_devices.
        CHECK: Assert it handles the error and returns an empty list.
        """
        mock_rm = MagicMock()
        mock_rm.list_resources.side_effect = Exception("USB scan error")
        
        devices = discover_usb_devices(mock_rm)
        self.assertEqual(devices, [])

if __name__ == '__main__':
    unittest.main()
