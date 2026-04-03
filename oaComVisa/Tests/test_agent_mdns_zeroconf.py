# oaComVisa/Tests/test_agent_mdns_zeroconf.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the mDNS and IP discovery functions in agent_mdns_zeroconf.py.

import unittest
from unittest.mock import MagicMock, patch, call
import socket

from oaComVisa.Workers.agent_mdns_zeroconf import AES70DiscoveryListener, discover_aes70_devices, discover_ip_devices

class TestAgentMdnsZeroconf(unittest.TestCase):

    def test_aes70_discovery_listener(self):
        """Test the AES70DiscoveryListener callbacks."""
        listener = AES70DiscoveryListener()
        mock_zc = MagicMock()
        mock_info = MagicMock()
        mock_info.addresses = [socket.inet_aton("192.168.1.100")]
        mock_info.port = 1234
        mock_info.server = "test-server.local."
        mock_info.properties = {b"prop1": b"val1"}
        mock_zc.get_service_info.return_value = mock_info
        
        # Test add_service
        listener.add_service(mock_zc, "_oca._tcp.local.", "TestDevice")
        self.assertIn("TestDevice", listener.found_devices)
        dev = listener.found_devices["TestDevice"]
        self.assertEqual(dev["ip"], "192.168.1.100")
        self.assertEqual(dev["port"], 1234)
        self.assertEqual(dev["properties"]["prop1"], "val1")
        
        # Test remove_service
        listener.remove_service(mock_zc, "_oca._tcp.local.", "TestDevice")
        self.assertNotIn("TestDevice", listener.found_devices)

    @patch('oaComVisa.Workers.agent_mdns_zeroconf.Zeroconf')
    @patch('oaComVisa.Workers.agent_mdns_zeroconf.ServiceBrowser')
    @patch('oaComVisa.Workers.agent_mdns_zeroconf.time.sleep')
    def test_discover_aes70_devices(self, mock_sleep, MockBrowser, MockZeroconf):
        """Test discover_aes70_devices function."""
        # This is hard to test deeply without real zeroconf, but we can check the calls
        MockZeroconf.return_value = MagicMock()
        devices = discover_aes70_devices(timeout=0.1)
        
        MockZeroconf.assert_called_once()
        MockBrowser.assert_called_once()
        mock_sleep.assert_called_with(0.1)
        self.assertEqual(devices, {})

    @patch('oaComVisa.Workers.agent_mdns_zeroconf._get_local_ip')
    @patch('oaComVisa.Workers.agent_mdns_zeroconf._check_host')
    @patch('oaComVisa.Workers.agent_mdns_zeroconf.discover_aes70_devices')
    @patch('oaComVisa.Workers.agent_mdns_zeroconf.ThreadPoolExecutor')
    def test_discover_ip_devices(self, MockExecutor, mock_discover_aes, mock_check_host, mock_get_ip):
        """
        BUILD: Mock network scan and AES70 discovery.
        OPERATE: Call discover_ip_devices.
        CHECK: Assert it returns merged lists of dedicated and gateway IPs.
        """
        mock_get_ip.return_value = "192.168.1.50"
        
        # Mock executor to return a dedicated device from port scan
        executor = MockExecutor.return_value.__enter__.return_value
        mock_future = MagicMock()
        mock_future.result.return_value = ("192.168.1.100", "DEDICATED")
        executor.submit.return_value = mock_future
        # Simplify: assume only one target is scanned for this test to avoid massive mock loops
        with patch('oaComVisa.Workers.agent_mdns_zeroconf.range', return_value=[100]):
            
            # Mock AES70 to return another device
            mock_discover_aes.return_value = {
                "AES_DEV": {"ip": "192.168.1.200", "port": 1234}
            }
            
            dedicated, gateways = discover_ip_devices()
            
            self.assertIn("192.168.1.100", dedicated)
            self.assertIn("192.168.1.200", dedicated) # Merged from AES70
            self.assertEqual(len(dedicated), 2)

    @patch('socket.socket')
    @patch('oaComVisa.Workers.agent_mdns_zeroconf._get_local_ip', return_value="192.168.1.50")
    def test_check_host_dedicated(self, mock_get_ip, mock_socket_cls):
        """Test _check_host for a dedicated device (Port 5025)."""
        from oaComVisa.Workers.agent_mdns_zeroconf import _check_host
        
        # We need two different mock socket instances because they are created sequentially
        mock_sock1 = MagicMock()
        mock_sock1.__enter__.return_value = mock_sock1
        mock_sock1.connect_ex.return_value = 1 # Port 111 Fail
        
        mock_sock2 = MagicMock()
        mock_sock2.__enter__.return_value = mock_sock2
        mock_sock2.connect_ex.return_value = 0 # Port 5025 Success
        
        # When socket.socket() is called twice, return these two mocks
        mock_socket_cls.side_effect = [mock_sock1, mock_sock2]
        
        result = _check_host("192.168.1.100")
        self.assertEqual(result, ("192.168.1.100", "DEDICATED"))

if __name__ == '__main__':
    unittest.main()
