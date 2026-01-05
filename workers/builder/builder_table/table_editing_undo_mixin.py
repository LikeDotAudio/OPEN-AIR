import tkinter as tk
import inspect
import orjson

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service

class TableEditingUndoMixin:
    def __init__(self):
        self.undo_stack = []

    def undo(self, event=None):
        if not self.undo_stack: return
        last_action = self.undo_stack.pop()
        
        if last_action["action"] == "edit":
            # Revert Tree
            # Use display_col_name from last_action for setting value
            self.tree.set(last_action["row"], last_action["display_col_name"], last_action["old"])

            # Revert MQTT
            # Get current values of the row after reverting the tree
            current_values_after_undo = list(self.tree.item(last_action["row"], 'values'))
            
            # Reconstruct row_data as a dictionary
            row_data_after_undo = {self.tree["columns"][i]: current_values_after_undo[i] 
                                    for i in range(len(self.tree["columns"]))}
            
            item_tags = self.tree.item(last_action["row"], 'tags')
            device_key = item_tags[0] if item_tags else None

            if self.data_topic and device_key:
                field_topic = get_topic(self.data_topic, "data", device_key)
                mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(row_data_after_undo))
                debug_logger(
                    message=f"MQTT Reverted: topic='{field_topic}', payload='{row_data_after_undo}'",
                    **_get_log_args()
                )
            
            debug_logger(message="⏪ Undo successful!", **_get_log_args())
        elif last_action["action"] == "delete":
            # Revert Tree: Re-insert the row
            device_key = last_action["device_key"]
            old_row_data = last_action["old_row_data"]
            
            # Convert dict values to a list in the order of current headers
            headers = self.tree["columns"]
            values_to_insert = [old_row_data.get(h, "") for h in headers]

            # Re-insert the row (Treeview generates a new item_id)
            new_item_id = self.tree.insert('', tk.END, values=values_to_insert, tags=(device_key,))
            
            # Publish the old row data to MQTT
            if self.data_topic and device_key:
                field_topic = get_topic(self.data_topic, "data", device_key)
                mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(old_row_data))
                debug_logger(
                    message=f"MQTT Restored (Undo Delete): topic='{field_topic}', payload='{old_row_data}'",
                    **_get_log_args()
                )
            debug_logger(message=f"⏪ Undo: Re-inserted row for device {device_key}.", **_get_log_args())
        elif last_action["action"] == "add":
            item_id = last_action["item_id"]
            device_key = last_action["device_key"]
            if self.tree.exists(item_id):
                self.tree.delete(item_id)
                
                # Publish a "clear" payload to MQTT to remove the added row
                if self.data_topic and device_key:
                    field_topic = get_topic(self.data_topic, "data", device_key)
                    mqtt_publisher_service.publish_payload(field_topic, orjson.dumps({})) # Publish empty dict for clear
                    debug_logger(
                        message=f"MQTT Removed (Undo Add): topic='{field_topic}', payload='{{}}'",
                        **_get_log_args()
                    )
                debug_logger(message=f"⏪ Undo: Removed added row with item_id: {item_id}, device_key: {device_key}.", **_get_log_args())
