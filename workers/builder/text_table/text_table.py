# text_table/table.py
#
# A mixin for creating an editable table widget with CSV functionality, synchronized via MQTT.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260220.Industrial.1

import tkinter as tk
from tkinter import ttk
import inspect
import orjson
import os
import re

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from workers.Command_Router.mqtt import mqtt_publisher_service
from workers.Command_Router.mqtt.mqtt_message import MqttMessage
from .table_editing_manager import TableEditingManager  # Import the new brain
from managers.Display.transparency.transparency_mixin import TransparencyMixin

# New CSV Imports
from .Table_CSV_Writer import TableCsvWriter
from .Table_CSV_Reader import TableCsvReader
from .Table_CSV_check import TableCsvCheck

import workers.initialization.worker_project_paths as app_paths

CSV_SAVE_DIR = str(app_paths.TABLES_DIR)


class BuilderTextTableCreator(TransparencyMixin):
    """Mixin class for creating an editable table widget with CSV functionality."""

    def make_text_table(self, parent_widget, config_data, context=None, **kwargs):
        """Creates an editable table widget."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️📑 [BUILDER] Entering make_text_table")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        # Extract widget-specific config from config_data
        label = config_data.get("label_active") or config_data.get("path") or "Table"
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️📑 [BUILDER] Materializing editable table '{label}' at path '{path}'.")

        # 1. Main Container (Canvas for Industrial Transparency)
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating main canvas container for table '{label}'")
        container = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat")
        container.grid_rowconfigure(0, weight=1)  # Row for the treeview
        container.grid_columnconfigure(0, weight=1)
        
        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to table container.")
            self._apply_transparency(container, container, config, builder_instance)

        # ⚡ OPTIMIZATION: Use engine to calculate absolute topic (handles absolute paths)
        absolute_data_topic = state_mirror_engine.calculate_topic(path, base_mqtt_topic_from_path)
        
        # Calculate "Room" topic (the parent topic of this widget)
        room_topic = get_topic(getattr(state_mirror_engine, "base_topic", "OPEN-AIR"), base_mqtt_topic_from_path)

        # 2. Treeview setup
        table_height = config.get("height", 10)
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Instantiating ttk.Treeview table (Height: {table_height}).")
        tree = ttk.Treeview(container, show="headings", height=table_height, style="Custom.Treeview")

        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        # --- Internal State ---
        item_map = {}  # Maps tree item IDs to row data
        device_key_map = {}  # Maps unique keys (e.g. model/serial) to tree item IDs
        self._is_reading_csv = False  # Guard to prevent MQTT feedback loops during CSV load

        # CSV Path setup
        clean_label = re.sub(r"[^a-zA-Z0-9]", "_", label)
        csv_path = os.path.join(CSV_SAVE_DIR, f"{clean_label}.csv")
        if BUILDER_DEBUG: builder_logger.debug(f"📂💾✨ [DATA] Local CSV backup path: {csv_path}")

        # Instantiate Helpers
        csv_reader = TableCsvReader()
        csv_writer = TableCsvWriter()
        csv_checker = TableCsvCheck()

        # Attach Editing Manager
        if BUILDER_DEBUG: builder_logger.trace("🏗️⚙️📝 [CONSTRUCT] Attaching TableEditingManager brain.")
        tree.editor = TableEditingManager(
            tree,
            state_mirror_engine,
            absolute_data_topic,
            allow_sort=config.get("allow_sort", True),
            allow_undo=config.get("allow_undo", True),
            allow_delete=config.get("allow_delete", True),
        )

        def _handle_write_csv():
            """Gathers all data from the tree and writes to CSV."""
            if BUILDER_DEBUG: builder_logger.trace(f"🔄💾✨ [DATA] Writing table data to CSV backup.")
            data_to_save = list(item_map.values())
            headers = list(tree["columns"])
            if headers:
                csv_writer.write_to_csv(csv_path, headers, data_to_save)

        def _handle_read_csv():
            """Reads from CSV and updates the table."""
            if BUILDER_DEBUG: builder_logger.info(f"🔄📂✨ [DATA] Reading table data from CSV backup.")
            self._is_reading_csv = True
            headers, data = csv_reader.read_from_csv(csv_path)
            if data:
                # Convert list of rows to dict for update_table_full
                data_dict = {}
                key_preference = ["gpib_address", "serial_number", "resource_string", "model", "id"]
                for i, row in enumerate(data):
                    item_key = None
                    for k in key_preference:
                        if k in row and row[k]:
                            item_key = row[k]
                            break
                    if not item_key:
                        item_key = f"row_{i}"
                    data_dict[item_key] = row

                update_table_full(data_dict)
            self._is_reading_csv = False

        # --- Button Frame ---
        button_frame = tk.Frame(container, bd=0, highlightthickness=0)
        
        def sync_bg():
            if not container.winfo_exists(): return
            if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing table background and styles.")
            bg = container.cget("bg")
            button_frame.config(bg=bg)
            # Treeview might need style update if background changes significantly
            style = ttk.Style()
            style.configure("Custom.Treeview", background=bg, fieldbackground=bg)
        
        container._draw = sync_bg
        
        buttons_added = False
        if config.get("write_cvs", True):
            ttk.Button(button_frame, text="Write to CSV", command=_handle_write_csv).pack(side=tk.LEFT, padx=5)
            buttons_added = True

        if config.get("read_cvs", True):
            ttk.Button(button_frame, text="Read from CSV", command=_handle_read_csv).pack(side=tk.LEFT, padx=5)
            buttons_added = True

        if config.get("Add_Row", True):
            ttk.Button(button_frame, text="Add Row", command=tree.editor.add_row).pack(side=tk.LEFT, padx=5)
            buttons_added = True

        if config.get("Delete_Row", True):
            ttk.Button(button_frame, text="Delete Row", command=tree.editor.delete_selection).pack(side=tk.LEFT, padx=5)
            buttons_added = True

        if config.get("Undo", True):
            ttk.Button(button_frame, text="Undo", command=tree.editor.undo).pack(side=tk.LEFT, padx=5)
            buttons_added = True

        if buttons_added:
            button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        # Immediately set headers from config if they exist
        initial_headers = config.get("headers", [])
        if initial_headers:
            if BUILDER_DEBUG: builder_logger.debug(f"📐🔡✨ [LAYOUT] Applying initial headers: {initial_headers}")
            tree["columns"] = initial_headers
            for col in initial_headers:
                tree.heading(col, text=col)
                tree.column(col, width=120, minwidth=60, stretch=tk.YES, anchor="w")

        # --- INITIALIZATION LOGIC ---
        if absolute_data_topic:
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Checking CSV integrity for topic: {absolute_data_topic}")
            csv_checker.initialize_from_csv(csv_path, initial_headers, absolute_data_topic)

        def update_table_full(payload):
            if BUILDER_DEBUG: builder_logger.debug(f"🔄✨📑 [SYNC] Executing FULL table update for '{label}'")
            try:
                if isinstance(payload, str): data = orjson.loads(payload)
                elif isinstance(payload, bytes): data = orjson.loads(payload.decode("utf-8"))
                else: data = payload

                if not isinstance(data, dict): return

                for i in tree.get_children(): tree.delete(i)
                item_map.clear()
                device_key_map.clear()

                if not data:
                    _handle_write_csv()
                    return

                columns = tree["columns"]
                if not columns and data:
                    first_item_key = next(iter(data))
                    first_item = data[first_item_key]
                    columns = list(first_item.keys())
                    tree["columns"] = columns
                    for col in columns:
                        tree.heading(col, text=col)
                        tree.column(col, width=120, minwidth=60, stretch=tk.YES, anchor="w")

                for item_key, item_value in data.items():
                    values = [item_value.get(col, "") for col in columns]
                    item_id = tree.insert("", tk.END, values=values, tags=(item_key))
                    item_map[item_id] = item_value
                    device_key_map[item_key] = item_id

                    if absolute_data_topic and not self._is_reading_csv:
                        field_topic = get_topic(absolute_data_topic, "data", item_key)
                        if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Publishing full update for member: {field_topic}")
                        mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(item_value).decode())

                _handle_write_csv()
            except Exception as e:
                if BUILDER_DEBUG:
                    builder_logger.exception(f"❌🚫🛑 [ERROR] failure in full table update for '{label}'")

        def update_table_incremental(msg: MqttMessage):
            topic = msg.topic
            payload = msg.payload
            if BUILDER_DEBUG: builder_logger.trace(f"📥📶🔄 [MQTT] Incoming incremental update on: {topic}")
            try:
                if isinstance(payload, bytes): data = orjson.loads(payload.decode("utf-8"))
                elif isinstance(payload, str): data = orjson.loads(payload)
                else: data = payload
            except: return

            if topic.endswith("/selected"): return
            
            pulse_angle = data.get("angle") or data.get("position")
            if isinstance(data, dict) and data.get("pulse") is True and pulse_angle is not None:
                angle = pulse_angle
                if BUILDER_DEBUG: builder_logger.trace(f"🌀🔄✨ [SYNC] Pulse detected at {angle:.1f}°. Finding target row.")
                target_id = None
                try:
                    angle_key = str(int(angle)) 
                    if angle_key in device_key_map: target_id = device_key_map[angle_key]
                except: pass
                
                if not target_id:
                    angle_col = next((col for col in tree["columns"] if col.lower() in ["angle", "deg", "degree", "position", "rotation"]), None)
                    if angle_col:
                        for item_id, item_data in item_map.items():
                            try:
                                if abs(float(item_data.get(angle_col)) - float(angle)) < 1.0:
                                    target_id = item_id
                                    break
                            except: pass
                if target_id:
                    if BUILDER_DEBUG: builder_logger.trace(f"🎯🔳✨ [VIEW] Auto-selecting row for pulse angle: {angle:.1f}°")
                    tree.selection_set(target_id)
                    tree.see(target_id)
                return

            if not absolute_data_topic: return
            data_prefix = absolute_data_topic + "/data/"
            if topic == absolute_data_topic or not topic.startswith(data_prefix): return

            device_key = topic[len(data_prefix) :]
            if "/" in device_key: return

            if not data and data is not False and data != 0:
                if device_key in device_key_map:
                    if BUILDER_DEBUG: builder_logger.info(f"❌🧹📑 [MQTT] Removing row for key: {device_key}")
                    item_id = device_key_map.pop(device_key)
                    if item_id in item_map: del item_map[item_id]
                    tree.delete(item_id)
                _handle_write_csv()
                return

            if not tree["columns"]:
                columns = list(data.keys())
                tree["columns"] = columns
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, width=120, minwidth=60, stretch=tk.YES, anchor="w")

            values = [data.get(col, "") for col in tree["columns"]]
            if device_key in device_key_map:
                if BUILDER_DEBUG: builder_logger.trace(f"✨🔄📑 [MQTT] Updating row for key: {device_key}")
                item_id = device_key_map[device_key]
                tree.item(item_id, values=values)
                item_map[item_id] = data
            else:
                if BUILDER_DEBUG: builder_logger.trace(f"➕🏗️📑 [MQTT] Inserting new row for key: {device_key}")
                item_id = tree.insert("", tk.END, values=values, tags=(device_key))
                item_map[item_id] = item_value # wait, item_value is not defined here, it should be data
                item_map[item_id] = data
                device_key_map[device_key] = item_id
            _handle_write_csv()

        def on_select(event):
            selection = tree.selection()
            if selection:
                selected_item_id = selection[0]
                selected_label = tree.item(selected_item_id, "values")[0] if tree.item(selected_item_id, "values") else "Unknown"
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆📑 [INPUT] User selected table row: '{selected_label}'")
                selected_data = item_map.get(selected_item_id)
                if selected_data and path:
                    # ⚡ CONSISTENCY: Use engine to calculate absolute topic for selection
                    absolute_selected_topic = state_mirror_engine.calculate_topic(f"{path}/selected", base_mqtt_topic_from_path)
                    if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Broadcasting selection state to: {absolute_selected_topic}")
                    mqtt_publisher_service.publish_payload(absolute_selected_topic, orjson.dumps({"val": selected_data}).decode())

        if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding selection protocol to table.")
        tree.bind("<<TreeviewSelect>>", on_select)

        if path:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering table at path '{path}'")
            widget_id = path
            dummy_var = tk.StringVar()
            state_mirror_engine.register_widget(widget_id, dummy_var, base_mqtt_topic_from_path, config, update_callback=update_table_full)

            if absolute_data_topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to incremental updates: {absolute_data_topic}/#")
                subscriber_router.subscribe_to_topic(absolute_data_topic + "/#", update_table_incremental)
                
            if room_topic and room_topic != absolute_data_topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to ROOM updates: {room_topic}/#")
                subscriber_router.subscribe_to_topic(room_topic + "/#", update_table_incremental)

            def _cleanup(event):
                if event.widget == str(container):
                    if BUILDER_DEBUG: builder_logger.trace(f"❌🧹📡 [CLEANUP] Unsubscribing table topics for '{path}'")
                    if absolute_data_topic:
                        subscriber_router.unsubscribe_from_topic(absolute_data_topic + "/#", update_table_incremental)
                    if room_topic and room_topic != absolute_data_topic:
                        subscriber_router.unsubscribe_from_topic(room_topic + "/#", update_table_incremental)

            container.bind("<Destroy>", _cleanup)

            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing table state from cache/broker.")
            if not state_mirror_engine.initialize_widget_state(widget_id):
                static_data = config.get("data")
                if static_data: 
                    if BUILDER_DEBUG: builder_logger.debug(f"📦🆗✅ [DATA] Loading static table data from config.")
                    update_table_full(static_data)
                else: _handle_write_csv()

            selected_topic_path = path + "/selected"
            selected_var = tk.StringVar()
            state_mirror_engine.register_widget(selected_topic_path, selected_var, base_mqtt_topic_from_path, {"type": "_GuiValue"})
            state_mirror_engine.initialize_widget_state(selected_topic_path)

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗📑 [SUCCESS] The editable table '{label}' has materialized!")
        return container
