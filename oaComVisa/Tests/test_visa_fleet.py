import unittest
from unittest.mock import MagicMock, patch
from oaComVisa.Visa_Fleet.visa_fleet import FleetOrchestrator

class TestVisaFleet(unittest.TestCase):
    def setUp(self):
        self.mqtt = MagicMock()
        self.router = MagicMock()
        with patch("oaComVisa.Visa_Fleet.visa_fleet.DiscoveryOrchestrator"), \
             patch("oaComVisa.Visa_Fleet.visa_fleet.VisaJsonBuilder.load_inventory_from_json", return_value=[]):
            self.fleet = FleetOrchestrator(self.mqtt, self.router)

    def test_inventory_notification(self):
        """Goal: Verify that the fleet correctly notifies and persists new inventory data."""
        # Setup mocks for internal builders
        self.fleet.json_builder = MagicMock()
        self.fleet.csv_builder = MagicMock()
        self.fleet.mqtt_bridge = MagicMock()
        
        test_device = {"IDN": "TEK,DPO123", "RESOURCE": "USB::123"}
        self.fleet.json_builder.augment_device_details.return_value = {"model": "DPO123", "serial": "123"}
        
        # Trigger notification (normally called after scan)
        self.fleet._notify_inventory([test_device])
        
        # CHECK: Builders called
        self.fleet.json_builder.save_inventory_to_json.assert_called()
        self.fleet.csv_builder.build_csvs_from_json.assert_called()
        # CHECK: MQTT Bridge notified
        self.fleet.mqtt_bridge.publish_inventory.assert_called()

if __name__ == "__main__":
    unittest.main()
