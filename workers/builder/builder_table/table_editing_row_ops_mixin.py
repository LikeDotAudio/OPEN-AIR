import tkinter as tk
import inspect
import orjson
import re

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service

class TableEditingRowOpsMixin:
    def __init__(self):
        pass # No specific state needed for this mixin's __init__

    def add_row(self):
        current_function = inspect.currentframe().f_code.co_name
        debug_logger(message="➕ Adding new row.", **_get_log_args())

        # Determine next available device_key (simple incremental for now)
        next_device_num = 1
        existing_keys = set()
        for item_id in self.tree.get_children():
            tags = self.tree.item(item_id, 'tags')
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
        new_item_id = self.tree.insert('', tk.END, values=values_to_insert, tags=(device_key,))

        # Add to undo stack - self.undo_stack will be defined in the main TableEditingManager
        self.undo_stack.append({
            "action": "add",
            "item_id": new_item_id, # Store the actual Treeview item ID
            "device_key": device_key,
            "row_data": new_row_data # Store the data for potential redo/revert if needed
        })
        
        # Publish to MQTT - self.data_topic and self.state_mirror_engine will be in main TableEditingManager
        if self.data_topic and device_key:
            field_topic = get_topic(self.data_topic, "data", device_key)
            mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(new_row_data))
            debug_logger(
                message=f"MQTT Added: topic='{field_topic}', payload='{new_row_data}'",
                **_get_log_args()
            )

        debug_logger(message=f"➕ Added new row with item_id: {new_item_id}, device_key: {device_key}", **_get_log_args())
        
        # Select the new row and start editing the first cell
        self.tree.selection_set(new_item_id)
        if headers:
            # Assuming start_edit is available from InplaceMixin
            self.start_edit(new_item_id, '#1')

    def delete_selection(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            debug_logger(message="🗑️ No items selected for deletion.", **_get_log_args())
            return

        for item_id in selected_items:
            # Get data for undo purposes
            item_values = self.tree.item(item_id, 'values')
            item_tags = self.tree.item(item_id, 'tags')
            device_key = item_tags[0] if item_tags else None

            # Push delete action to undo stack (store full row data)
            if device_key: # Only track if we have a device key
                # Reconstruct row_data as a dictionary
                headers = self.tree["columns"]
                old_row_data = {headers[i]: item_values[i] for i in range(len(headers))}
                self.undo_stack.append({
                    "action": "delete",
                    "row_id": item_id, # Keep track of old item_id for re-insertion, though Treeview will assign new one
                    "device_key": device_key,
                    "old_row_data": old_row_data
                })

                # Publish a "clear" payload to MQTT
                field_topic = get_topic(self.data_topic, "data", device_key)
                mqtt_publisher_service.publish_payload(field_topic, orjson.dumps({})) # Publish empty dict for clear
                debug_logger(
                    message=f"MQTT Deleted: topic='{field_topic}', payload='{{}}'",
                    **_get_log_args()
                )

            # Delete from Treeview
            self.tree.delete(item_id)
            debug_logger(message=f"🗑️ Deleted row {item_id} (Device Key: {device_key}).", **_get_log_args())
        
        debug_logger(message="🗑️ Delete selection completed.", **_get_log_args())

    def import_data(self, data_list):
        current_function = inspect.currentframe().f_code.co_name
        debug_logger(message=f"➕ Importing {len(data_list)} new rows.", **_get_log_args())

        headers = self.tree["columns"]
        
        # Iterate through the data to import
        for row_data_dict in data_list:
            # Generate a unique device_key (similar to add_row)
            next_device_num = 1
            existing_keys = set()
            for item_id in self.tree.get_children():
                tags = self.tree.item(item_id, 'tags')
                if tags:
                    existing_keys.add(tags[0])
            
            while f"imported_row_{next_device_num}" in existing_keys:
                next_device_num += 1
            
            device_key = f"imported_row_{next_device_num}"

            # Prepare values for Treeview insertion
            values_to_insert = [row_data_dict.get(h, "") for h in headers]

            # Insert into Treeview
            new_item_id = self.tree.insert('', tk.END, values=values_to_insert, tags=(device_key,))

            # Add to undo stack (as an 'add' action)
            self.undo_stack.append({
                "action": "add",
                "item_id": new_item_id,
                "device_key": device_key,
                "row_data": row_data_dict
            })
            
            # Publish to MQTT
            if self.data_topic and device_key:
                field_topic = get_topic(self.data_topic, "data", device_key)
                mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(row_data_dict))
                debug_logger(
                    message=f"MQTT Imported: topic='{field_topic}', payload='{row_data_dict}'",
                    **_get_log_args()
                )
        debug_logger(message=f"➕ Finished importing {len(data_list)} rows.", **_get_log_args())
