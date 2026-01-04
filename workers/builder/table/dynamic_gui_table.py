# workers/builder/table/dynamic_gui_table.py
import tkinter as tk
from tkinter import ttk
import inspect
import orjson

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt import mqtt_publisher_service

class GuiTableCreatorMixin:
    """Mixin class for creating an editable table widget."""

    def _create_gui_table(self, parent_frame, label, config, path, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router):
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(message=f"Creating editable table widget: {label}", **_get_log_args())

        container = ttk.Frame(parent_frame)
        container.grid_rowconfigure(0, weight=1)
        data_topic = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)

        table_height = config.get("height", 10)
        tree = ttk.Treeview(container, show='headings', height=table_height, style="Custom.Treeview")

        # Immediately set headers from config if they exist
        initial_headers = config.get("headers", [])
        if initial_headers:
            tree['columns'] = initial_headers
            for col in initial_headers:
                tree.heading(col, text=col)
                tree.column(col, width=120, minwidth=60, stretch=tk.YES, anchor='w')
            debug_logger(message=f"--- Table '{label}' initialized with headers from config.", **_get_log_args())

        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        item_map = {}  # Maps treeview item ID to device data dict
        device_key_map = {} # Maps device key to treeview item ID

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

                    if data_topic:
                        field_topic = get_topic(data_topic, item_key)
                        mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(item_value))
                
                debug_logger(message=f"--- Table '{label}' updated with {len(data)} rows.", **_get_log_args())
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

        def on_double_click(event):
            region = tree.identify("region", event.x, event.y)
            if region != "cell":
                return

            column_id = tree.identify_column(event.x)
            if not column_id:
                return
            column_index = int(column_id.replace('#', '')) - 1
            selected_iid = tree.focus()
            
            if not selected_iid:
                return
            
            if column_index < 0 or column_index >= len(tree['columns']):
                return

            column_name = tree['columns'][column_index]
            item_data = item_map.get(selected_iid, {})
            device_key = ""
            for key, iid in device_key_map.items():
                if iid == selected_iid:
                    device_key = key
                    break
            
            x, y, width, height = tree.bbox(selected_iid, column_id)
            
            entry_var = tk.StringVar(value=item_data.get(column_name, ""))
            entry = ttk.Entry(tree, textvariable=entry_var)
            entry.place(x=x, y=y, width=width, height=height)
            entry.focus_set()

            def on_entry_commit(event=None):
                new_value = entry_var.get()
                tree.set(selected_iid, column=column_id, value=new_value)
                item_map[selected_iid][column_name] = new_value

                if device_key and path:
                    if data_topic:
                        payload_to_publish = item_map[selected_iid]
                        field_topic = get_topic(data_topic, device_key)
                        mqtt_publisher_service.publish_payload(field_topic, orjson.dumps(payload_to_publish))
                entry.destroy()

            entry.bind("<Return>", on_entry_commit)
            entry.bind("<FocusOut>", on_entry_commit)

        tree.bind('<<TreeviewSelect>>', on_select)
        tree.bind('<Double-1>', on_double_click)

        if path:
            widget_id = path
            dummy_var = tk.StringVar()
            
            data_topic = get_topic(state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)

            state_mirror_engine.register_widget(widget_id, dummy_var, base_mqtt_topic_from_path, config, update_callback=update_table_full)
            
            subscriber_router.subscribe_to_topic(data_topic + "/#", update_table_incremental)
            debug_logger(message=f"Table '{label}' subscribed to data topic '{data_topic}/#'", **_get_log_args())

            # Let the state mirror engine handle initialization
            if not state_mirror_engine.initialize_widget_state(widget_id):
                # if initialize_widget_state returns false (meaning no cached data was loaded)
                # then load static data.
                static_data = config.get("data")
                if static_data:
                    update_table_full(static_data)
            
            # Register the 'selected' topic
            selected_topic_path = path + "/selected"
            selected_var = tk.StringVar() # This will hold a JSON string
            selected_config = {"type": "_Value"} 
            state_mirror_engine.register_widget(selected_topic_path, selected_var, base_mqtt_topic_from_path, selected_config)
            state_mirror_engine.initialize_widget_state(selected_topic_path)

        return container
