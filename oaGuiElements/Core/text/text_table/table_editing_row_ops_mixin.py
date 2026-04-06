# text_table/table_editing_row_ops_mixin.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: text_table/table_editing_row_ops_mixin.py

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import inspect
import orjson

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import TABLE_LOGGER
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaComMQTT.Core import mqtt_publisher_service


class TableEditingRowOpsMixin:
    # Initializes the TableEditingRowOpsMixin.
    # This mixin does not require any specific state initialization in its constructor.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def __init__(self):
        pass  # No specific state needed for this mixin's __init__

    # Adds a new empty row to the Treeview table.
    # This method generates a unique key for the new row, creates an empty row
    # adds the action to the undo stack, and publishes the new row via MQTT.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def add_row(self):
        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Adding new row.", "DEBUG")

        # Determine next available device_key (simple incremental for now)
        next_device_num = 1
        existing_keys = set()
        for item_id in self.tree.get_children():
            tags = self.tree.item(item_id, "tags")
            if tags:
                existing_keys.add(tags[0])

        while f"new_row_{next_device_num}" in existing_keys:
            next_device_num += 1

        device_key = f"new_row_{next_device_num}"

        # Create an empty row with default values
        headers = self.tree["columns"]
        new_row_data = {header: "" for header in headers}
        if "NAME" in new_row_data:
            new_row_data["NAME"] = f"New Item {next_device_num}"
        elif headers:
            new_row_data[headers[0]] = f"New Item {next_device_num}"

        values_to_insert = [new_row_data.get(h, "") for h in headers]

        # Insert into Treeview
        new_item_id = self.tree.insert(
            "", tk.END, values=values_to_insert, tags=(device_key)
        )

        # Add to undo stack - self.undo_stack will be defined in the main TableEditingManager
        self.undo_stack.append(
            {
                "action": "add",
                "item_id": new_item_id,  # Store the actual Treeview item ID
                "device_key": device_key,
                "row_data": new_row_data,  # Store the data for potential redo/revert if needed
            }
        )

        # Publish to MQTT - self.data_topic and self.state_mirror_engine will be in main TableEditingManager
        if self.data_topic and device_key and self.state_mirror_engine:
            field_topic = self.state_mirror_engine.calculate_topic(f"data/{device_key}", self.data_topic)
            mqtt_publisher_service.publish_payload(
                field_topic, orjson.dumps(new_row_data).decode()
            )
            matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"MQTT Added: topic='{field_topic}', payload='{new_row_data}'", "DEBUG")

        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Added new row with item_id: {new_item_id}, device_key: {device_key}", "DEBUG")

        # Select the new row and start editing the first cell
        self.tree.selection_set(new_item_id)
        if headers:
            # Assuming start_edit is available from InplaceMixin
            self.start_edit(new_item_id, "#1")

    # Deletes the currently selected rows from the Treeview table.
    # This method iterates through selected rows, stores their data for undo purposes,
    # publishes a "clear" payload to MQTT for each deleted row, and then removes them
    # Inputs:
    #     event: The tkinter event object (optional).
    # Outputs:
    #     None.
    def delete_selection(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "No items selected for deletion.", "DEBUG")
            return

        for item_id in selected_items:
            # Get data for undo purposes
            item_values = self.tree.item(item_id, "values")
            item_tags = self.tree.item(item_id, "tags")
            device_key = item_tags[0] if item_tags else None

            # Push delete action to undo stack (store full row data)
            if device_key:  # Only track if we have a device key
                # Reconstruct row_data as a dictionary
                headers = self.tree["columns"]
                old_row_data = {headers[i]: item_values[i] for i in range(len(headers))}
                self.undo_stack.append(
                    {
                        "action": "delete",
                        "row_id": item_id,  # Keep track of old item_id for re-insertion, though Treeview will assign new one
                        "device_key": device_key,
                        "old_row_data": old_row_data,
                    }
                )

                # Publish a "clear" payload to MQTT
                if self.state_mirror_engine:
                    field_topic = self.state_mirror_engine.calculate_topic(f"data/{device_key}", self.data_topic)
                    mqtt_publisher_service.publish_payload(
                        field_topic, orjson.dumps({}).decode()
                    )  # Publish empty dict for clear
                matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"MQTT Deleted: topic='{field_topic}', payload='{{}}'", "DEBUG")

            # Delete from Treeview
            self.tree.delete(item_id)
            matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Deleted row {item_id} (Device Key: {device_key}).", "DEBUG")

        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Delete selection completed.", "DEBUG")

    # Imports data from a list of dictionaries into the Treeview table.
    # This method processes a list of dictionaries (e.g., from a CSV import),
    # generating unique keys for each row, inserting them into the Treeview,
    # adding the import action to the undo stack, and publishing each row via MQTT.
    # Inputs:
    #     data_list (list): A list of dictionaries, where each dictionary is a row of data to import.
    # Outputs:
    #     None.
    def import_data(self, data_list):
        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Importing {len(data_list)} new rows.", "DEBUG")

        headers = self.tree["columns"]

        # Iterate through the data to import
        for row_data_dict in data_list:
            # Generate a unique device_key (similar to add_row)
            next_device_num = 1
            existing_keys = set()
            for item_id in self.tree.get_children():
                tags = self.tree.item(item_id, "tags")
                if tags:
                    existing_keys.add(tags[0])

            while f"imported_row_{next_device_num}" in existing_keys:
                next_device_num += 1

            device_key = f"imported_row_{next_device_num}"

            # Prepare values for Treeview insertion
            values_to_insert = [row_data_dict.get(h, "") for h in headers]

            # Insert into Treeview
            new_item_id = self.tree.insert(
                "", tk.END, values=values_to_insert, tags=(device_key)
            )

            # Add to undo stack (as an 'add' action)
            self.undo_stack.append(
                {
                    "action": "add",
                    "item_id": new_item_id,
                    "device_key": device_key,
                    "row_data": row_data_dict,
                }
            )

            # Publish to MQTT
            if self.data_topic and device_key and self.state_mirror_engine:
                field_topic = self.state_mirror_engine.calculate_topic(f"data/{device_key}", self.data_topic)
                mqtt_publisher_service.publish_payload(
                    field_topic, orjson.dumps(row_data_dict).decode()
                )
                matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"MQTT Imported: topic='{field_topic}', payload='{row_data_dict}'", "DEBUG")
        matrix_log("ui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Finished importing {len(data_list)} rows.", "DEBUG")