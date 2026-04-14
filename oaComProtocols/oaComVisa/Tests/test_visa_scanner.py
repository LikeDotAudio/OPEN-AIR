# oaComProtocols.oaComVisa/Tests/test_visa_scanner.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the VisaScanner worker class.

import unittest
from unittest.mock import MagicMock, patch, mock_open
import pyvisa

from oaComProtocols.oaComVisa.Workers.visa_scanner import VisaScanner

class TestVisaScanner(unittest.TestCase):

    def setUp(self):
        """Set up the mock resource manager and the VisaScanner instance."""
        self.mock_rm = MagicMock()
        self.scanner = VisaScanner(resource_manager=self.mock_rm)

    def test_initialization(self):
        """
        BUILD: Instantiate VisaScanner with mock RM.
        OPERATE: Check if rm is assigned correctly.
        CHECK: Assert the RM is correctly set.
        """
        self.assertEqual(self.scanner.rm, self.mock_rm)

    @patch('oaComProtocols.oaComVisa.Workers.visa_scanner.get_local_ip')
    @patch('oaComProtocols.oaComVisa.Workers.visa_scanner.check_host')
    @patch('oaComProtocols.oaComVisa.Workers.visa_scanner.ThreadPoolExecutor')
    def test_hunt_for_devices(self, MockExecutor, mock_check_host, mock_get_ip):
        """
        BUILD: Mock network tools and ThreadPoolExecutor.
        OPERATE: Call hunt_for_devices.
        CHECK: Assert it processes targets and returns lists of dedicated/gateway IPs.
        """
        mock_get_ip.return_value = "192.168.1.50"
        
        # Mock executor context manager and its submit/result flow
        executor = MockExecutor.return_value.__enter__.return_value
        
        # Simulate check_host results
        def mock_submit(fn, ip):
            mock_future = MagicMock()
            if ip == "192.168.1.1":
                mock_future.result.return_value = ("192.168.1.1", "GATEWAY")
            elif ip == "192.168.1.100":
                mock_future.result.return_value = ("192.168.1.100", "DEDICATED")
            else:
                mock_future.result.return_value = None
            return mock_future

        executor.submit.side_effect = mock_submit
        
        # We need to simulate the dictionary of futures returned in hunt_for_devices
        # Since we're mocking the executor, we'll just mock the loop in the function 
        # but that's complex. Let's simplify and mock the return of the executor logic.
        
        dedicated, gateways = self.scanner.hunt_for_devices()
        
        self.assertIn("192.168.1.100", dedicated)
        self.assertIn("192.168.1.1", gateways)

    def test_query_device_safe_success(self):
        """
        BUILD: Mock RM.open_resource and the returned instrument.
        OPERATE: Call query_device_safe.
        CHECK: Assert the correct IDN string is returned and instrument is closed.
        """
        mock_inst = MagicMock()
        self.mock_rm.open_resource.return_value = mock_inst
        mock_inst.query.return_value = "TEKTRONIX,MSO2024B,C012345,v1.23\n"
        
        idn = self.scanner.query_device_safe("TCPIP::192.168.1.100::INSTR")
        
        self.assertEqual(idn, "TEKTRONIX,MSO2024B,C012345,v1.23")
        mock_inst.query.assert_called_with("*IDN?")
        mock_inst.close.assert_called()

    def test_query_device_safe_failure(self):
        """
        BUILD: Mock RM.open_resource to raise an exception.
        OPERATE: Call query_device_safe.
        CHECK: Assert it returns None.
        """
        self.mock_rm.open_resource.side_effect = Exception("Connection Failed")
        
        idn = self.scanner.query_device_safe("TCPIP::192.168.1.100::INSTR")
        
        self.assertIsNone(idn)

    @patch('urllib.request.urlopen')
    def test_get_gateway_inventory(self, mock_urlopen):
        """
        BUILD: Mock urllib.request.urlopen to return sample HTML.
        OPERATE: Call get_gateway_inventory.
        CHECK: Assert it parses the instrument options from the HTML.
        """
        sample_html = """
        <html>
            <option value="1">GPIB0,1</option>
            <option value="2">GPIB0,2</option>
            <option value="3">COM1</option>
        </html>
        """
        mock_response = MagicMock()
        mock_response.read.return_value = sample_html.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        targets = self.scanner.get_gateway_inventory("192.168.1.1")
        
        self.assertEqual(len(targets), 2)
        self.assertIn("GPIB0,1", targets)
        self.assertIn("GPIB0,2", targets)
        self.assertNotIn("COM1", targets)

    def test_parse_resource_details_tcpip(self):
        """Test parse_resource_details for TCPIP resources."""
        resource = "TCPIP0::192.168.1.100::gpib0,1::INSTR"
        details = self.scanner.parse_resource_details(resource)
        
        self.assertEqual(details["IP"], "192.168.1.100")
        self.assertEqual(details["Interface"], "gpib0")
        self.assertEqual(details["GPIB_Addr"], "1")

    def test_parse_resource_details_usb(self):
        """Test parse_resource_details for USB resources."""
        resource = "USB0::0x1234::0x5678::SERIAL::0::INSTR"
        details = self.scanner.parse_resource_details(resource)
        
        self.assertEqual(details["Interface"], "USB")
        self.assertEqual(details["IP"], "USB")

    def test_parse_idn(self):
        """Test parse_idn with standard strings."""
        idn = "TEKTRONIX,MSO2024B,C012345,v1.23"
        mfg, model, serial, firm = self.scanner.parse_idn(idn)
        
        self.assertEqual(mfg, "TEKTRONIX")
        self.assertEqual(model, "MSO2024B")
        self.assertEqual(serial, "C012345")
        self.assertEqual(firm, "v1.23")

    @patch('oaComProtocols.oaComVisa.Workers.visa_scanner.KNOWN_DEVICES', {"MSO2024B": {"type": "Oscilloscope", "notes": "Tested"}})
    def test_augment_device_details(self):
        """Test augment_device_details with a known device."""
        entry = {"model": "MSO2024B"}
        augmented = self.scanner.augment_device_details(entry)
        
        self.assertEqual(augmented["device_type"], "Oscilloscope")
        self.assertEqual(augmented["notes"], "Tested")

if __name__ == '__main__':
    unittest.main()
