from loguru import logger

class FleetInventoryMixin:
    """Manages the inventory of fleet devices in JSON and CSV formats."""

    @property
    def current_inventory(self):
        """Retrieves the most recent fleet inventory list."""
        return self._current_inventory

    def _notify_inventory(self, inventory_data):
        """Updates the global inventory, persists it to disk, and publishes to MQTT."""
        augmented_inventory = []
        for device_entry in inventory_data:
            augmented_inventory.append(
                self.json_builder.augment_device_details(device_entry)
            )

        self._current_inventory = augmented_inventory
        self.json_builder.save_inventory_to_json(augmented_inventory)
        self.csv_builder.build_csvs_from_json()
        grouped_inventory = self.json_builder.load_grouped_inventory_from_json()

        self.cb_inventory(augmented_inventory)
        self.mqtt_bridge.publish_inventory(grouped_inventory)

    def _notify_response(self, serial, response, command, corr_id):
        self.json_builder.save_query_response_to_json(serial, response, command, corr_id)
        self.cb_response(serial, response, command, corr_id)

    def _notify_error(self, serial, message, command):
        self.cb_error(serial, message, command)

    def _notify_status(self, serial, status):
        self.cb_status(serial, status)
