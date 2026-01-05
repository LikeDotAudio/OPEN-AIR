import tkinter as tk
from tkinter import ttk
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import orjson
import inspect
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service

class TableEditingManager:
    def __init__(self, tree, state_mirror_engine, data_topic):
        current_function = inspect.currentframe().f_code.co_name
        self.tree = tree
        self.state_mirror_engine = state_mirror_engine
        self.data_topic = data_topic
        self.undo_stack = []
        
        # State for header sorting
        self._sort_column_name = None
        self._sort_reverse = False

        # Bindings
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Delete>", self.delete_selection)
        self.tree.bind("<Control-z>", self.undo)
        
        # Setup Header Sorting
        self._bind_headers()
        debug_logger(
            message=f"📊 TableEditingManager initialized for tree {tree}",
            **_get_log_args()
        )

    def on_double_click(self, event):
        """Identify cell and spawn Entry widget"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        
        col = self.tree.identify_column(event.x) # Returns '#1'
        row_id = self.tree.identify_row(event.y)
        
        # Logic to spawn Entry widget over the cell...
        self.start_edit(row_id, col)

    def start_edit(self, row_id, col):
        if self.editing_entry:
            self.destroy_entry()  # Destroy any existing entry before creating a new one

        # Store active cell info
        self.active_row = row_id
        self.active_col = col

        # Get cell bounding box
        # Convert column identifier (e.g., '#1') to display column name
        display_col_index = int(col.replace('#', '')) - 1
        display_col_name = self.tree["columns"][display_col_index]

        x, y, width, height = self.tree.bbox(row_id, col)
        
        # Get current cell value
        current_value = self.tree.set(row_id, display_col_name) # Use display_col_name here

        # Create and place entry widget
        entry_var = tk.StringVar(value=current_value)
        self.editing_entry = ttk.Entry(self.tree, textvariable=entry_var)
        self.editing_entry.place(x=x, y=y, width=width, height=height)
        self.editing_entry.focus_set()

        # Bind events for committing or canceling edit
        self.editing_entry.bind("<Return>", self._on_entry_commit)
        self.editing_entry.bind("<FocusOut>", self._on_entry_commit)
        # Bind Shift-Return for auto-incrementing and committing
        self.editing_entry.bind("<Shift-Return>", self._on_entry_commit)

        debug_logger(
            message=f"📝 Starting edit for row {row_id}, col {col} with value '{current_value}'",
            **_get_log_args()
        )

    def commit_edit(self, new_value):
        if not self.active_row or not self.active_col:
            self.destroy_entry()
            return

        # Get old value for Undo Stack
        # Convert self.active_col (e.g., '#1') to column name
        display_col_index = int(self.active_col.replace('#', '')) - 1
        display_col_name = self.tree["columns"][display_col_index]
        old_value = self.tree.set(self.active_row, display_col_name)

        # Only proceed if the value actually changed
        if old_value == new_value:
            self.destroy_entry()
            return

        # Push to Undo Stack
        self.undo_stack.append({
            "action": "edit", 
            "row": self.active_row, 
            "col": self.active_col, 
            "display_col_name": display_col_name,
            "old": old_value, 
            "new": new_value
        })

        # Update Tree
        self.tree.set(self.active_row, display_col_name, new_value)
        
        # Update MQTT (State Mirror)
        # Get full row data to publish
        current_values = list(self.tree.item(self.active_row, 'values'))
        
        # Reconstruct row_data as a dictionary
        row_data = {self.tree["columns"][i]: current_values[i] 
                    for i in range(len(self.tree["columns"]))}
        
        # Determine the device_key from the row_id (assuming tags are used for device_key)
        # The dynamic_gui_table.py inserts item_id = tree.insert('', tk.END, values=values, tags=(item_key,))
        # So we can get the item_key from the tags
        item_tags = self.tree.item(self.active_row, 'tags')
        device_key = item_tags[0] if item_tags else None

        if self.data_topic and device_key:
            field_topic = get_topic(self.data_topic, "data", device_key)
            mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(row_data))
            debug_logger(
                message=f"MQTT Updated: topic='{field_topic}', payload='{row_data}'",
                **_get_log_args()
            )

        debug_logger(
            message=f"💾 Committed edit: row {self.active_row}, col {display_col_name}, new value {new_value}",
            **_get_log_args()
        )
        self.destroy_entry()

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
    
    def _bind_headers(self):
        for col_name in self.tree["columns"]:
            self.tree.heading(col_name, command=lambda c=col_name: self._sort_column(c))
        debug_logger(message="⬆️ Binding headers for sorting.", **_get_log_args())

    def _sort_column(self, col_name):
        current_function = inspect.currentframe().f_code.co_name
        debug_logger(message=f"Sorting column: {col_name}", **_get_log_args())

        # Get all items in the Treeview
        data = []
        for item_id in self.tree.get_children(''):
            values = self.tree.item(item_id, 'values')
            # Ensure the number of values matches columns
            if len(values) == len(self.tree["columns"]):
                # Create a dictionary for easier access by column name
                row_dict = {self.tree["columns"][i]: values[i] for i in range(len(values))}
                data.append((item_id, row_dict))
            else:
                debug_logger(message=f"Skipping row {item_id} due to column mismatch. Values: {values}", level="WARNING", **_get_log_args())

        if not data:
            return

        # Determine sort order
        if col_name == self._sort_column_name:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column_name = col_name
            self._sort_reverse = False # Default to ascending for new column

        # Sort the data
        # Use a more robust key function that handles mixed types (e.g., numbers vs strings)
        def get_sort_key(item_tuple):
            row_dict = item_tuple[1]
            value = row_dict.get(col_name, "")
            try:
                # Try to convert to float for numeric sorting
                return float(value)
            except (ValueError, TypeError):
                # Fallback to string for non-numeric values
                return str(value).lower()

        data.sort(key=get_sort_key, reverse=self._sort_reverse)

        # Rearrange items in the Treeview
        for index, (item_id, _) in enumerate(data):
            self.tree.move(item_id, '', index)

        # Update header arrow to indicate sort order
        # For now, just use text indicators, as images require more setup
        for c in self.tree["columns"]:
            if c == col_name:
                self.tree.heading(c, text=f"{c}{' ▼' if self._sort_reverse else ' ▲'}")
            else:
                # Remove arrow from other columns
                original_text = self.tree.heading(c, "text")
                self.tree.heading(c, text=re.sub(r' [▼▲]', '', original_text))
        
        debug_logger(message=f"Column '{col_name}' sorted {'descending' if self._sort_reverse else 'ascending'}.", **_get_log_args())

    def add_row(self):
        current_function = inspect.currentframe().f_code.co_name
        debug_logger(message="➕ Adding new row.", **_get_log_args())

        # Determine next available device_key (simple incremental for now)
        # This will need to be more robust for real applications,
        # e.g., checking existing keys, or using UUIDs.
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
        # Optionally, set a default value for the first column or 'NAME'
        if "NAME" in new_row_data:
            new_row_data["NAME"] = f"New Item {next_device_num}"
        elif headers:
            new_row_data[headers[0]] = f"New Item {next_device_num}"

        values_to_insert = [new_row_data.get(h, "") for h in headers]
        
        # Insert into Treeview
        new_item_id = self.tree.insert('', tk.END, values=values_to_insert, tags=(device_key,))

        # Add to undo stack
        self.undo_stack.append({
            "action": "add",
            "item_id": new_item_id, # Store the actual Treeview item ID
            "device_key": device_key,
            "row_data": new_row_data # Store the data for potential redo/revert if needed
        })
        
        # Publish to MQTT
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
            self.start_edit(new_item_id, '#1') # Start editing the first column of the new row

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

    def destroy_entry(self):
        if self.editing_entry:
            self.editing_entry.destroy()
            self.editing_entry = None
            self.active_row = None
            self.active_col = None
            debug_logger(message="📝 Editing entry destroyed.", **_get_log_args())

    def _increment_string_with_trailing_digits(self, text):
        """
        Increments any trailing digits in a string. If no trailing digits, appends '1'.
        e.g., "Mic 1" -> "Mic 2", "Camera" -> "Camera 1", "Ch 09" -> "Ch 10"
        """
        match = re.search(r'(\d+)$', text)
        if match:
            num_str = match.group(1)
            prefix = text[:-len(num_str)]
            incremented_num = int(num_str) + 1
            # Preserve leading zeros
            new_num_str = str(incremented_num).zfill(len(num_str))
            return f"{prefix}{new_num_str}"
        else:
            return f"{text} 1"