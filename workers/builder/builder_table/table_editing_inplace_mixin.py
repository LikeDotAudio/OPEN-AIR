import tkinter as tk
from tkinter import ttk
import inspect
import orjson
import re

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service


class TableEditingInplaceMixin:
    def __init__(self):
        # State for active editing
        self.editing_entry = None
        self.active_row = None
        self.active_col = None

    def on_double_click(self, event):
        """Identify cell and spawn Entry widget"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)  # Returns '#1'
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
        display_col_index = int(col.replace("#", "")) - 1
        display_col_name = self.tree["columns"][display_col_index]

        x, y, width, height = self.tree.bbox(row_id, col)

        # Get current cell value
        current_value = self.tree.set(
            row_id, display_col_name
        )  # Use display_col_name here

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
            **_get_log_args(),
        )

    def commit_edit(self, new_value):
        if not self.active_row or not self.active_col:
            self.destroy_entry()
            return

        # Get old value for Undo Stack
        # Convert self.active_col (e.g., '#1') to column name
        display_col_index = int(self.active_col.replace("#", "")) - 1
        display_col_name = self.tree["columns"][display_col_index]
        old_value = self.tree.set(self.active_row, display_col_name)

        # Only proceed if the value actually changed
        if old_value == new_value:
            self.destroy_entry()
            return

        # Push to Undo Stack - self.undo_stack will be defined in the main TableEditingManager
        self.undo_stack.append(
            {
                "action": "edit",
                "row": self.active_row,
                "col": self.active_col,
                "display_col_name": display_col_name,
                "old": old_value,
                "new": new_value,
            }
        )

        # Update Tree
        self.tree.set(self.active_row, display_col_name, new_value)

        # Update MQTT (State Mirror) - self.data_topic and self.state_mirror_engine will be in main TableEditingManager
        current_values = list(self.tree.item(self.active_row, "values"))
        row_data = {
            self.tree["columns"][i]: current_values[i]
            for i in range(len(self.tree["columns"]))
        }
        item_tags = self.tree.item(self.active_row, "tags")
        device_key = item_tags[0] if item_tags else None

        if self.data_topic and device_key:
            field_topic = get_topic(self.data_topic, "data", device_key)
            self.state_mirror_engine.publish_payload(
                field_topic, orjson.dumps(row_data)
            )  # publish_payload from state_mirror_engine
            debug_logger(
                message=f"MQTT Updated: topic='{field_topic}', payload='{row_data}'",
                **_get_log_args(),
            )

        debug_logger(
            message=f"💾 Committed edit: row {self.active_row}, col {display_col_name}, new value {new_value}",
            **_get_log_args(),
        )
        self.destroy_entry()

    def _on_entry_commit(self, event=None):
        if not self.editing_entry:
            return

        new_value = self.editing_entry.get()

        if event and event.keysym == "Return" and (event.state & 0x0001):
            new_value = self._increment_string_with_trailing_digits(new_value)
            debug_logger(
                message=f"Auto-incremented value to: {new_value}", **_get_log_args()
            )

        self.commit_edit(new_value)

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
        match = re.search(r"(\d+)$", text)
        if match:
            num_str = match.group(1)
            prefix = text[: -len(num_str)]
            incremented_num = int(num_str) + 1
            # Preserve leading zeros
            new_num_str = str(incremented_num).zfill(len(num_str))
            return f"{prefix}{new_num_str}"
        else:
            return f"{text} 1"
