# oaComProtocols.oaComVisa/Tests/test_agent_static_ip_prober.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the discover_gateway_devices function.

import unittest
from unittest.mock import MagicMock, patch
import urllib.request

from oaComProtocols.oaComVisa.Workers.agent_static_ip_prober import discover_gateway_devices

class TestAgentStaticIpProber(unittest.TestCase):

    @patch('urllib.request.urlopen')
    def test_discover_gateway_devices_success(self, mock_urlopen):
        """
        BUILD: Mock urllib.request.urlopen to return sample HTML for two gateways.
        OPERATE: Call discover_gateway_devices.
        CHECK: Assert the correctly formatted TCPIP resource strings are returned.
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
        
        gateway_ips = ["192.168.1.1", "192.168.1.2"]
        resources = discover_gateway_devices(gateway_ips)
        
        # We expect 2 resources per gateway = 4 total
        self.assertEqual(len(resources), 4)
        self.assertIn("TCPIP::192.168.1.1::GPIB0,1::INSTR", resources)
        self.assertIn("TCPIP::192.168.1.1::GPIB0,2::INSTR", resources)
        self.assertIn("TCPIP::192.168.1.2::GPIB0,1::INSTR", resources)
        self.assertIn("TCPIP::192.168.1.2::GPIB0,2::INSTR", resources)
        self.assertNotIn("TCPIP::192.168.1.1::COM1::INSTR", resources)

    @patch('urllib.request.urlopen')
    def test_discover_gateway_devices_exception(self, mock_urlopen):
        """
        BUILD: Mock urlopen to raise an exception for one gateway.
        OPERATE: Call discover_gateway_devices.
        CHECK: Assert it continues and returns resources from other gateways if available.
        """
        mock_urlopen.side_effect = [Exception("Network error"), MagicMock()]
        
        gateway_ips = ["192.168.1.1", "192.168.1.2"]
        # The second call will succeed but return no matches (default MagicMock mock_response)
        resources = discover_gateway_devices(gateway_ips)
        
        self.assertEqual(len(resources), 0)
        self.assertEqual(mock_urlopen.call_count, 2)

if __name__ == '__main__':
    unittest.main()
