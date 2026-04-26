# Core/fleet_inventory_manager.py
# Author: Anthony Peter Kuzub
# Version: 2.0.0
#
# Description: Refactored Inventory Manager (Composition over Inheritance).


class InventoryManager:
    """Manages the inventory of fleet devices in JSON and CSV formats."""

    def __init__(self, orchestrator):
        self._orchestrator = orchestrator
        self._current_inventory = []

    @property
    def current_inventory(self):
        """Retrieves the most recent fleet inventory list."""
        return self._current_inventory

    def notify_inventory(self, inventory_data):
        """Updates the global inventory, persists it to disk, and publishes to MQTT."""
        augmented_inventory = []
        for device_entry in inventory_data:
            augmented_inventory.append(
                self._orchestrator.json_builder.augment_device_details(device_entry)
            )

        self._current_inventory = augmented_inventory
        self._orchestrator.json_builder.save_inventory_to_json(augmented_inventory)
        self._orchestrator.csv_builder.build_csvs_from_json()
        grouped_inventory = self._orchestrator.json_builder.load_grouped_inventory_from_json()

        self._orchestrator.cb_inventory(augmented_inventory)
        self._orchestrator.mqtt_bridge.publish_inventory(grouped_inventory)

    def notify_response(self, serial, response, command, corr_id):
        self._orchestrator.json_builder.save_query_response_to_json(serial, response, command, corr_id)
        self._orchestrator.cb_response(serial, response, command, corr_id)

    def notify_error(self, serial, message, command):
        self._orchestrator.cb_error(serial, message, command)

    def notify_status(self, serial, status):
        self._orchestrator.cb_status(serial, status)
