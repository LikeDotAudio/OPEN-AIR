# workers/builder/builder_table/dynamic_gui_table.py
import tkinter as tk
from tkinter import ttk
import inspect
import orjson
import os
import re

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service
from .table_editing_manager import TableEditingManager # Import the new brain

# New CSV Imports
from .Table_CSV_Writer import TableCsvWriter
from .Table_CSV_Reader import TableCsvReader
from .Table_CSV_check import TableCsvCheck

CSV_SAVE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "OPEN-AIR", "DATA", "Tables")

class GuiTableCreatorMixin:
    """Mixin class for creating an editable table widget with CSV functionality."""

    def _create_gui_table(self, parent_widget, config_data): # Updated signature
        current_function_name = inspect.currentframe().f_code.co_name
        
        # Extract arguments from config_data
        label = config_data.get("label_active") # Use label_active from config_data
        config = config_data # config_data is the config
        path = config_data.get("path")
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        debug_logger(message=f"Creating editable table widget: {label}", **_get_log_args())

        container = ttk.Frame(parent_widget) # Use parent_widget here
        container.grid_rowconfigure(0, weight=1) # Row for the treeview
        container.grid_columnconfigure(0, weight=1)

        data_topic = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)

        table_height = config.get("height", 10)
        tree = ttk.Treeview(container, show='headings', height=table_height, style="Custom.Treeview")

        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, columnspan=2, sticky='ew')

        # ⚡ ATTACH THE FLUX CAPACITOR (Editor) ⚡
        data_topic_for_editor = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)
        
        # Store the editor instance on the tree so it doesn't get garbage collected
        tree.editor = TableEditingManager(tree, state_mirror_engine, data_topic_for_editor)

        item_map = {}  # Maps treeview item ID to device data dict
        device_key_map = {} # Maps device key to treeview item ID
        
        self._is_reading_csv = False # Flag to prevent feedback loops

        # --- CSV Functionality Setup ---
        csv_writer = TableCsvWriter()
        csv_reader = TableCsvReader()
        csv_checker = TableCsvCheck()
        
        # Sanitize the data_topic to create a valid filename
        sanitized_topic = re.sub(r'[^a-zA-Z0-9_-]', '_', data_topic)
        csv_path = os.path.join(CSV_SAVE_DIR, f"{sanitized_topic}.csv")

        def _handle_write_csv():
            if self._is_reading_csv:
                return # Don't save while reading from a file
                
            headers = tree['columns']
            data_to_write = list(item_map.values())
            if headers: # Only write if there are headers
                csv_writer.write_to_csv(csv_path, headers, data_to_write)

        def _handle_read_csv():
            headers, data_list = csv_reader.read_from_csv(csv_path)
            if not data_list:
                debug_logger(message=f"No data read from CSV '{csv_path}'.", **_get_log_args())
                return
            
            # Reconstruct the dictionary format that update_table_full expects
            reconstructed_data = {}
            key_preference = ['gpib_address', 'serial_number', 'resource_string']
            
            for i, row in enumerate(data_list):
                key_found = False
                for key_name in key_preference:
                    if key_name in row and row[key_name]:
                        reconstructed_data[row[key_name]] = row
                        key_found = True
                        break
                if not key_found:
                    # Fallback key if preferred keys are not found
                    reconstructed_data[f"row_{i}"] = row
            
            try:
                self._is_reading_csv = True
                update_table_full(reconstructed_data)
            finally:
                self._is_reading_csv = False


        # --- Button Frame ---
        button_frame = ttk.Frame(container)
        button_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5,0))
        
        write_button = ttk.Button(button_frame, text="Write to CSV", command=_handle_write_csv)
        write_button.pack(side=tk.LEFT, padx=5)

        read_button = ttk.Button(button_frame, text="Read from CSV", command=_handle_read_csv)
        read_button.pack(side=tk.LEFT, padx=5)

        add_row_button = ttk.Button(button_frame, text="Add Row", command=tree.editor.add_row)
        add_row_button.pack(side=tk.LEFT, padx=5)

        delete_row_button = ttk.Button(button_frame, text="Delete Row", command=tree.editor.delete_selection)
        delete_row_button.pack(side=tk.LEFT, padx=5)

        undo_button = ttk.Button(button_frame, text="Undo", command=tree.editor.undo)
        undo_button.pack(side=tk.LEFT, padx=5)


        # Immediately set headers from config if they exist
        initial_headers = config.get("headers", [])
        if initial_headers:
            tree['columns'] = initial_headers
            for col in initial_headers:
                tree.heading(col, text=col)
                tree.column(col, width=120, minwidth=60, stretch=tk.YES, anchor='w')
            debug_logger(message=f"--- Table '{label}' initialized with headers from config.", **_get_log_args())
        
        # --- NEW INITIALIZATION LOGIC ---
        # 1. Check for CSV and publish its contents to seed the state cache
        csv_checker.initialize_from_csv(csv_path, initial_headers, data_topic)

        def update_table_full(payload):
            debug_logger(message=f"--- Calling update_table_full for '{label}' with payload: {payload}", **_get_log_args())
            try:
                if isinstance(payload, str):
                    data = orjson.loads(payload)
                elif isinstance(payload, bytes):
                    debug_logger(message="--- Payload is bytes, decoding.", **_get_log_args())
                    data = orjson.loads(payload.decode('utf-8'))
                else:
                    data = payload
                debug_logger(message=f"--- Data for full update: {data}", **_get_log_args())

                if not isinstance(data, dict):
                    debug_logger(message=f"Invalid data format for table '{label}'. Expected dict.", level="WARNING", **_get_log_args())
                    return

                debug_logger(message="--- Clearing tree.", **_get_log_args())
                for i in tree.get_children():
                    tree.delete(i)
                item_map.clear()
                device_key_map.clear()

                if not data:
                    debug_logger(message=f"--- Table '{label}' cleared (no data), but headers preserved.", **_get_log_args())
                    _handle_write_csv() # Auto-save blank state
                    return

                columns = tree['columns']
                # If columns aren't set for some reason, derive from data as a fallback.
                if not columns and data:
                    debug_logger(message="--- Columns not pre-configured. Deriving from data as fallback.", **_get_log_args())
                    first_item_key = next(iter(data))
                    first_item = data[first_item_key]
                    columns = list(first_item.keys())
                    tree['columns'] = columns
                    for col in columns:
                        tree.heading(col, text=col)
                        tree.column(col, width=120, minwidth=60, stretch=tk.YES, anchor='w')

                debug_logger(message="--- Populating rows and publishing static data if data_topic is present.", **_get_log_args())
                for item_key, item_value in data.items():
                    values = [item_value.get(col, "") for col in columns]
                    item_id = tree.insert('', tk.END, values=values, tags=(item_key,))
                    item_map[item_id] = item_value
                    device_key_map[item_key] = item_id

                    if data_topic and not self._is_reading_csv:
                        field_topic = get_topic(data_topic, "data", item_key)
                        mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(item_value))
                
                debug_logger(message=f"--- Table '{label}' updated with {len(data)} rows.", **_get_log_args())
                _handle_write_csv() # Auto-save
            except Exception as e:
                debug_logger(message=f"Error doing full table update for '{label}': {e}", level="ERROR", **_get_log_args())

        def update_table_incremental(topic, payload):
            debug_logger(message=f"--- Calling update_table_incremental for '{label}' on topic '{topic}'", **_get_log_args())
            try:
                if topic.endswith("/selected"):
                    return
                    
                # Handle new topics like .../Table/data/23
                data_prefix = data_topic + '/data/'
                if not topic.startswith(data_prefix):
                    debug_logger(message=f"--- Topic '{topic}' does not match data prefix '{data_prefix}', ignoring.", **_get_log_args())
                    return
                
                device_key = topic[len(data_prefix):]
                # Ignore deeper nested topics
                if '/' in device_key:
                    debug_logger(message=f"--- Topic '{topic}' has extra segments, ignoring.", **_get_log_args())
                    return

                debug_logger(message=f"--- Device key: {device_key}", **_get_log_args())

                if not payload:
                    debug_logger(message="--- Empty payload, deleting row.", **_get_log_args())
                    if device_key in device_key_map:
                        item_id = device_key_map.pop(device_key)
                        if item_id in item_map:
                            del item_map[item_id]
                        tree.delete(item_id)
                        debug_logger(message=f"--- Deleted device '{device_key}' from table '{label}'.", **_get_log_args())
                    _handle_write_csv() # Auto-save
                    return

                if isinstance(payload, bytes):
                    data = orjson.loads(payload.decode('utf-8'))
                elif isinstance(payload, str):
                    data = orjson.loads(payload)
                else:
                    data = payload
                debug_logger(message=f"--- Incremental data: {data}", **_get_log_args())
                
                if not tree['columns']:
                    debug_logger(message="--- First time update, setting columns.", **_get_log_args())
                    columns = list(data.keys())
                    tree['columns'] = columns
                    for col in columns:
                        tree.heading(col, text=col)
                        tree.column(col, width=120, minwidth=60, stretch=tk.YES, anchor='w')

                values = [data.get(col, "") for col in tree['columns']]

                if device_key in device_key_map:
                    debug_logger(message=f"--- Updating device '{device_key}'.", **_get_log_args())
                    item_id = device_key_map[device_key]
                    tree.item(item_id, values=values)
                    item_map[item_id] = data
                else:
                    debug_logger(message=f"--- Adding new device '{device_key}'.", **_get_log_args())
                    item_id = tree.insert('', tk.END, values=values, tags=(device_key,))
                    item_map[item_id] = data
                    device_key_map[device_key] = item_id
                
                _handle_write_csv() # Auto-save
            except Exception as e:
                debug_logger(message=f"Error doing incremental table update for '{label}': {e}", level="ERROR", **_get_log_args())

        def on_select(event):
            selection = tree.selection()
            if selection:
                selected_item_id = selection[0]
                selected_data = item_map.get(selected_item_id)
                if selected_data and path:
                    selected_topic = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path, "selected")
                    payload = {"val": selected_data}
                    mqtt_publisher_service.publish_payload(selected_topic, orjson.dumps(payload))



        if path:
            widget_id = path
            dummy_var = tk.StringVar()
            
            state_mirror_engine.register_widget(widget_id, dummy_var, base_mqtt_topic_from_path, config, update_callback=update_table_full)
            
            subscriber_router.subscribe_to_topic(data_topic + "/#", update_table_incremental)
            debug_logger(message=f"Table '{label}' subscribed to data topic '{data_topic}/#'", **_get_log_args())

            # If static data exists in the config, publish it as the default state.
            static_data = config.get("data")
            if static_data:
                debug_logger(message=f"--- Found static data for '{label}'. Publishing as default state.", **_get_log_args())
                for item_key, item_value in static_data.items():
                    field_topic = get_topic(data_topic, "data", item_key)
                    mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(item_value))

            # Let the state mirror engine handle initialization
            if not state_mirror_engine.initialize_widget_state(widget_id):
                # if initialize_widget_state returns false (meaning no cached data was loaded)
                # then load static data from config. This will also auto-save.
                static_data = config.get("data")
                if static_data:
                    update_table_full(static_data)
                else: #If there is no static data either, ensure a blank CSV is created
                    _handle_write_csv()

            
            # Register the 'selected' topic
            selected_topic_path = path + "/selected"
            selected_var = tk.StringVar() # This will hold a JSON string
            selected_config = {"type": "_Value"} 
            state_mirror_engine.register_widget(selected_topic_path, selected_var, base_mqtt_topic_from_path, selected_config)
            state_mirror_engine.initialize_widget_state(selected_topic_path)

        return container
