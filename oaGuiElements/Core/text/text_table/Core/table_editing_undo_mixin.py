# text_table/table_editing_undo_mixin.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: text_table/table_editing_undo_mixin.py

import inspect
import tkinter as tk

import orjson

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaComProtocols.oaComMQTT.Core import mqtt_publisher_service


class TableEditingUndoMixin:
    # Initializes the TableEditingUndoMixin.
    # This sets up an empty list to serve as the undo stack, which stores a history of table modifications.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def __init__(self):
        self.undo_stack = []

    # Undoes the last editing action performed on the Treeview table.
    # This method pops the last action from the undo stack and reverts the Treeview
    # and corresponding MQTT state to its previous condition, supporting edits, additions, and deletions.
    # Inputs:
    #     event: The tkinter event object (optional).
    # Outputs:
    #     None.
    def undo(self, event=None):
        if not self.undo_stack:
            return
        last_action = self.undo_stack.pop()

        if last_action["action"] == "edit":
            # Revert Tree
            # Use display_col_name from last_action for setting value
            self.tree.set(
                last_action["row"], last_action["display_col_name"], last_action["old"]
            )

            # Revert MQTT
            # Get current values of the row after reverting the tree
            current_values_after_undo = list(
                self.tree.item(last_action["row"], "values")
            )

            # Reconstruct row_data as a dictionary
            row_data_after_undo = {
                self.tree["columns"][i]: current_values_after_undo[i]
                for i in range(len(self.tree["columns"]))
            }

            item_tags = self.tree.item(last_action["row"], "tags")
            device_key = item_tags[0] if item_tags else None

            if self.data_topic and device_key and self.state_mirror_engine:
                field_topic = self.state_mirror_engine.calculate_topic(f"data/{device_key}", self.data_topic)
                mqtt_publisher_service.publish_payload(
                    field_topic, orjson.dumps(row_data_after_undo).decode()
                )
                matrix_log("gui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"MQTT Reverted: topic='{field_topic}', payload='{row_data_after_undo}'", "DEBUG")

            matrix_log("gui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "Undo successful!", "SUCCESS")
        elif last_action["action"] == "delete":
            # Revert Tree: Re-insert the row
            device_key = last_action["device_key"]
            old_row_data = last_action["old_row_data"]

            # Convert dict values to a list in the order of current headers
            headers = self.tree["columns"]
            values_to_insert = [old_row_data.get(h, "") for h in headers]

            # Re-insert the row (Treeview generates a new item_id)
            new_item_id = self.tree.insert(
                "", tk.END, values=values_to_insert, tags=(device_key)
            )

            # Publish the old row data to MQTT
            if self.data_topic and device_key and self.state_mirror_engine:
                field_topic = self.state_mirror_engine.calculate_topic(f"data/{device_key}", self.data_topic)
                mqtt_publisher_service.publish_payload(
                    field_topic, orjson.dumps(old_row_data).decode()
                )
                matrix_log("gui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"MQTT Restored (Undo Delete): topic='{field_topic}', payload='{old_row_data}'", "DEBUG")
            matrix_log("gui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Undo: Re-inserted row for device {device_key}.", "DEBUG")
        elif last_action["action"] == "add":
            item_id = last_action["item_id"]
            device_key = last_action["device_key"]
            if self.tree.exists(item_id):
                self.tree.delete(item_id)

                # Publish a "clear" payload to MQTT to remove the added row
                if self.data_topic and device_key and self.state_mirror_engine:
                    field_topic = self.state_mirror_engine.calculate_topic(f"data/{device_key}", self.data_topic)
                    mqtt_publisher_service.publish_payload(
                        field_topic, orjson.dumps({}).decode()
                    )  # Publish empty dict for clear
                    matrix_log("gui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"MQTT Removed (Undo Add): topic='{field_topic}', payload='{{}}'", "DEBUG")
                matrix_log("gui", "gui_elements", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"Undo: Removed added row with item_id: {item_id}, device_key: {device_key}.", "DEBUG")
