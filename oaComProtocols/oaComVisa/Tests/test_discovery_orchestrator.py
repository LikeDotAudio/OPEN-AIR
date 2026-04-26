# oaComProtocols.oaComVisa/Tests/test_discovery_orchestrator.py
# Author: Gemini (Collaborator)
# Version: 20260323.0000.1
#
# Description: Tests for the DiscoveryOrchestrator class.

import unittest
from unittest.mock import MagicMock, patch

from oaComProtocols.oaComVisa.Managers.discovery_orchestrator import DiscoveryOrchestrator


class TestDiscoveryOrchestrator(unittest.TestCase):

    def setUp(self):
        """Set up the orchestrator with mocked dependencies."""
        self.mock_manager = MagicMock()
        self.mock_aes70 = MagicMock()

        # Patch VisaScanner where it's used inside DiscoveryOrchestrator
        patcher = patch('oaComProtocols.oaComVisa.Managers.discovery_orchestrator.VisaScanner')
        self.MockVisaScanner = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_scanner = self.MockVisaScanner.return_value

        self.orchestrator = DiscoveryOrchestrator(
            manager_ref=self.mock_manager,
            aes70_manager=self.mock_aes70,
            output_filename="test_inventory.json"
        )

    def test_run_discovery_success(self):
        """
        BUILD: Configure mock scanner to return some dummy IP/USB devices and successful responses.
        OPERATE: Call run_discovery.
        CHECK: Verify that the scanner methods were called and the inventory is built correctly.
        """
        self.mock_scanner.hunt_for_devices.return_value = (["192.168.1.100"], ["192.168.1.1"])
        self.mock_scanner.get_gateway_inventory.return_value = ["inst0", "inst1"]

        mock_rm = MagicMock()
        mock_rm.list_resources.return_value = ["USB0::0x1234::0x5678::INSTR", "TCPIP::192.168.1.50::INSTR"]
        self.mock_scanner.rm = mock_rm

        self.mock_scanner.parse_resource_details.return_value = {
            "IP": "192.168.1.100", "Interface": "TCPIP", "GPIB_Addr": "N/A"
        }
        self.mock_scanner.query_device_safe.return_value = "TestMfg,TestModel,12345,1.0"
        self.mock_scanner.parse_idn.return_value = ("TestMfg", "TestModel", "12345", "1.0")
        self.mock_scanner.augment_device_details.side_effect = lambda x: {**x, "device_type": "Oscilloscope", "notes": "OK"}

        # OPERATE
        inventory = self.orchestrator.run_discovery(silent=True)

        # CHECK
        self.assertTrue(self.mock_scanner.hunt_for_devices.called)
        self.assertTrue(self.mock_scanner.get_gateway_inventory.called)
        self.assertTrue(mock_rm.list_resources.called)

        # We expect: 1 dedicated, 2 gateway, 1 USB (TCPIP filtered out from list_resources)
        self.assertEqual(len(inventory), 4)

        # Check first device structure
        dev1 = inventory["1"]
        self.assertEqual(dev1["type"], "DEDICATED")
        self.assertEqual(dev1["status"], "Active")
        self.assertEqual(dev1["manufacturer"], "TestMfg")
        self.assertEqual(dev1["model"], "TestModel")

    def test_run_discovery_unresponsive(self):
        """
        BUILD: Configure mock scanner to simulate a device timeout (query_device_safe returns None).
        OPERATE: Call run_discovery.
        CHECK: Verify the device is marked as Unresponsive in the inventory.
        """
        self.mock_scanner.hunt_for_devices.return_value = (["10.0.0.5"], [])
        self.mock_scanner.get_gateway_inventory.return_value = []

        mock_rm = MagicMock()
        mock_rm.list_resources.return_value = []
        self.mock_scanner.rm = mock_rm

        self.mock_scanner.parse_resource_details.return_value = {
            "IP": "10.0.0.5", "Interface": "TCPIP", "GPIB_Addr": "N/A"
        }
        # Simulate timeout
        self.mock_scanner.query_device_safe.return_value = None

        inventory = self.orchestrator.run_discovery(silent=True)

        self.assertEqual(len(inventory), 1)
        dev1 = inventory["1"]
        self.assertEqual(dev1["status"], "Unresponsive")
        self.assertEqual(dev1["manufacturer"], "Unknown")
        self.assertEqual(dev1["notes"], "Connection Timed Out")

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('os.path.abspath', return_value='/fake/dir/discovery_orchestrator.py')
    def test_save_inventory(self, mock_abspath, mock_file):
        """
        BUILD: Populate the orchestrator's inventory.
        OPERATE: Call save_inventory.
        CHECK: Verify the file is opened for writing and the content is saved.
        """
        self.orchestrator.inventory = {"1": {"model": "TestModel"}}

        # OPERATE
        result_path = self.orchestrator.save_inventory()

        # CHECK
        self.assertEqual(result_path, '/fake/dir/test_inventory.json')
        mock_file.assert_called_once_with('/fake/dir/test_inventory.json', 'w', encoding='utf-8')
        mock_file().write.assert_called()

    def test_save_inventory_empty(self):
        """
        BUILD: Orchestrator with empty inventory.
        OPERATE: Call save_inventory.
        CHECK: Verify it returns False and doesn't try to write.
        """
        self.orchestrator.inventory = {}
        result = self.orchestrator.save_inventory()
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
