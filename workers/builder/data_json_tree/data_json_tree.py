# workers/builder/data_json_tree/data_json_tree.py
#
# A JSON Tree Viewer for the Dynamic GUI Builder.
# Displays JSON files or objects in a hierarchical ttk.Treeview.
# Supports Table View mode for structured data.
# Synchronizes data to MQTT topics.
#
# Author: Anthony Peter Kuzub
#
import orjson
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import os

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Command_Router.mqtt import mqtt_publisher_service
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic, TOPIC_DELIMITER
from managers.Display.transparency.transparency_mixin import TransparencyMixin

MAX_DEPTH = 5

class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself when it's not needed."""
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)

class BuilderDataJsonTreeCreator(TransparencyMixin):
    def make_data_json_tree(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a hierarchical tree view from a JSON file or object."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🗂️ [BUILDER] Entering make_data_json_tree")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        label = config_data.get("label_active")
        json_source = config_data.get("json_source")
        
        # 1. Parse 'ALLOW' Configuration
        allow_config = config_data.get("ALLOW", {})
        allow_browse = allow_config.get("browse", config_data.get("allow_browse", True))
        allow_filter = allow_config.get("filter", config_data.get("allow_filter", True))
        allow_edit = allow_config.get("edit", config_data.get("allow_edit", False))
        allow_save_as = allow_config.get("save_as", False)
        allow_expand_all = allow_config.get("expand_all", False)
        allow_table_toggle = allow_config.get("table_toggle", True)
        allow_mqtt_sync = allow_config.get("mqtt_sync", True)
        if BUILDER_DEBUG: builder_logger.debug(f"⚙️🔘✅ [CONFIG] Permissions: Browse={allow_browse}, Filter={allow_filter}, Edit={allow_edit}")
        
        # Initial View State
        show_values_var = tk.BooleanVar(value=config_data.get("show_values", False))
        
        tree_height = int(config_data.get("height", 20))
        
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")

        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [SCAFFOLD] Creating main frame for JSON Tree '{label}'")
        frame = tk.Frame(parent_widget)
        # frame.pack(fill=tk.BOTH, expand=True)  <-- REMOVED: Managed by AsyncGridRenderer
        
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

        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to JSON tree frame.")
            self._apply_transparency(frame, None, config_data, builder_instance)

        widget_path = config_data.get("path", "")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🗂️ [BUILDER] Spawning Data JSON Tree for '{label}' at path '{widget_path}'.")

        # State storage
        state = {
            "raw_data": None,
            "source_path": None,
            "dynamic_columns": []
        }

        # 1. Header
        header_frame = tk.Frame(frame)
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        if label and config_data.get("show_label", True):
            lbl = tk.Label(header_frame, text=label, font=("Helvetica", 10, "bold"), fg="white")
            lbl.pack(side=tk.LEFT, anchor="w")
            header_frame.lbl = lbl

        # 2. Filter & Controls Bar
        filter_frame = tk.Frame(frame)
        if allow_filter or allow_expand_all or allow_table_toggle:
            filter_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
            
            if allow_expand_all:
                def toggle_all(open_state):
                    if BUILDER_DEBUG: builder_logger.trace(f"🔄🗂️✨ [ACTION] Iteratively {'expanding' if open_state else 'collapsing'} all tree nodes.")
                    # Iterative stack-based toggle
                    stack = [child for child in tree.get_children("")]
                    while stack:
                        item = stack.pop()
                        tree.item(item, open=open_state)
                        stack.extend(tree.get_children(item))

                btn_expand = ttk.Button(filter_frame, text="Expand All", width=12, command=lambda: toggle_all(True))
                btn_expand.pack(side=tk.LEFT, padx=2)
                
                btn_collapse = ttk.Button(filter_frame, text="Collapse All", width=12, command=lambda: toggle_all(False))
                btn_collapse.pack(side=tk.LEFT, padx=2)

            if allow_table_toggle:
                def on_toggle_view():
                    if BUILDER_DEBUG: builder_logger.info(f"🔄📑🔳 [VIEW] Toggling JSON Tree view mode. Table View: {show_values_var.get()}")
                    # Full refresh required to rebuild columns
                    load_json_data(state["raw_data"])

                chk_table = ttk.Checkbutton(
                    filter_frame, text="Table View", 
                    variable=show_values_var, 
                    command=on_toggle_view
                )
                chk_table.pack(side=tk.LEFT, padx=5)
            
            if allow_filter:
                lbl_filter = tk.Label(filter_frame, text="Filter: ", font=("Arial", 8), fg="white")
                lbl_filter.pack(side=tk.LEFT)
                filter_var = tk.StringVar()
                filter_entry = ttk.Entry(filter_frame, textvariable=filter_var)
                filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                def on_filter_change(*args):
                    refresh_tree_display(filter_var.get())
                
                filter_var.trace_add("write", on_filter_change)

        # 3. Footer setup
        footer_frame = tk.Frame(frame)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # 4. Treeview setup
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        def sync_bg():
            if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing JSON tree components background.")
            bg = frame.cget("bg")
            header_frame.config(bg=bg)
            if hasattr(header_frame, 'lbl'): header_frame.lbl.config(bg=bg)
            filter_frame.config(bg=bg)
            for child in filter_frame.winfo_children():
                if isinstance(child, tk.Label): child.config(bg=bg)
            footer_frame.config(bg=bg)
            tree_frame.config(bg=bg)
            
            style = ttk.Style()
            style.configure("Custom.Treeview", background=bg, fieldbackground=bg)
        
        frame._draw = sync_bg
        
        vsb = AutoScrollbar(tree_frame, orient="vertical")
        hsb = AutoScrollbar(tree_frame, orient="horizontal")
        
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🗂️🔳 [CONSTRUCT] Instantiating ttk.Treeview.")
        tree = ttk.Treeview(
            tree_frame, 
            columns=("value"), 
            yscrollcommand=vsb.set, 
            xscrollcommand=hsb.set,
            style="Custom.Treeview",
            height=tree_height
        )
        
        tree.heading("#0", text="Key / Index", anchor="w")
        tree.heading("value", text="Value", anchor="w")
        tree.column("#0", width=250, minwidth=100, stretch=tk.YES)
        tree.column("value", width=250, minwidth=100, stretch=tk.YES)
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        def discover_columns(data):
            """Iteratively scans data to find common keys for table view."""
            state["dynamic_columns"] = []
            keys_found = set()
            
            # Stack contains (item, depth)
            stack = [(data, 0)]

            while stack:
                d, depth = stack.pop()
                if depth > 3: continue

                if isinstance(d, dict):
                    for k, v in d.items():
                        if isinstance(v, dict):
                            for sub_k in v.keys():
                                if not isinstance(v[sub_k], (dict, list)):
                                    keys_found.add(sub_k)
                        stack.append((v, depth + 1))
                elif isinstance(d, list):
                    for item in d:
                        if isinstance(item, dict):
                            for sub_k in item.keys():
                                if not isinstance(item[sub_k], (dict, list)):
                                    keys_found.add(sub_k)
                        stack.append((item, depth + 1))

            priority = ["name", "id", "Value", "Start_MHz", "Stop_MHz", "MHz", "channel"]
            cols = [k for k in priority if k in keys_found]
            cols += sorted([k for k in keys_found if k not in priority])
            state["dynamic_columns"] = cols

        def insert_node_iterative(data, filter_text=""):
            """Refactored iterative tree insertion with robust filtering and expansion."""
            filter_text = filter_text.lower()
            
            # Stack contains (parent_ui_id, key, value, depth)
            if isinstance(data, dict):
                items = list(reversed(list(data.items())))
                stack = [("", k, v, 0) for k, v in items]
            elif isinstance(data, list):
                items = list(reversed(list(enumerate(data))))
                stack = [("", f"[{i}]", v, 0) for i, v in items]
            else:
                return

            while stack:
                parent, key, value, depth = stack.pop()
                if depth > MAX_DEPTH: continue

                text_key = str(key)
                is_container = isinstance(value, (dict, list))
                str_val = str(value) if not is_container else ""
                
                # Filter match logic
                matches = not filter_text or (filter_text in text_key.lower() or filter_text in str_val.lower())
                
                # For containers, we should also check if any children match
                # (But checking deep children iteratively is complex, so we'll 
                # expand containers if the container name itself matches)
                is_open = bool(filter_text and matches)

                if is_container:
                    node_id = tree.insert(parent, "end", text=text_key, open=is_open)
                    if show_values_var.get() and isinstance(value, dict):
                        for col in state["dynamic_columns"]:
                            if col in value:
                                tree.set(node_id, col, str(value[col]))
                    
                    # Push children to stack
                    if isinstance(value, dict):
                        for k, v in reversed(list(value.items())):
                            stack.append((node_id, k, v, depth + 1))
                    else: # list
                        for i, v in reversed(list(enumerate(value))):
                            stack.append((node_id, f"[{i}]", v, depth + 1))
                else:
                    # Leaf node: Only show if it matches filter or filter is empty
                    if matches:
                        tree.insert(parent, "end", text=text_key, values=(str_val))

        def refresh_tree_display(filter_text=""):
            if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🔍 [VIEW] Refreshing tree display with filter: '{filter_text}'")
            tree.delete(*tree.get_children())
            data = state["raw_data"]
            if not data: return
            insert_node_iterative(data, filter_text)

        # def sync_to_mqtt():
        #     """Iteratively publishes all JSON data to MQTT topics."""
        #     if not state_mirror_engine or not state["raw_data"]: return
        #     
        #     base_topic = state_mirror_engine.calculate_topic(widget_path, base_mqtt_topic_from_path)
        #     
        #     if LOCAL_DEBUG: logger.debug(f"🌳📡 Starting Iterative MQTT Sync for {label} to {base_topic}")
        # 
        #     # Stack: [(data, current_topic, depth)]
        #     stack = [(state["raw_data"], base_topic, 0)]
        #     
        #     while stack:
        #         d, current_topic, depth = stack.pop()
        #         
        #         # Safety break
        #         if depth > MAX_DEPTH:
        #             continue
        # 
        #         # MQTT Sanitization
        #         sanitized_topic = current_topic.replace("+", "_").replace("#", "_")
        #         
        #         # Check if flat (leaf-like object)
        #         is_flat_obj = False
        #         if isinstance(d, (dict, list)):
        #             # Check shallow flatness
        #             if isinstance(d, dict):
        #                 is_flat_obj = not any(isinstance(v, (dict, list)) for v in d.values())
        #             else:
        #                 is_flat_obj = not any(isinstance(v, (dict, list)) for v in d)
        # 
        #         if is_flat_obj:
        #             try:
        #                 payload = {"val": d, "ts": 0, "src": "json-tree-sync"}
        #                 mqtt_publisher_service.publish_payload(sanitized_topic, orjson.dumps(payload).decode())
        #             except Exception as e:
        #                 pass # Log if needed
        #             continue
        # 
        #         # If not flat, traverse
        #         if isinstance(d, dict):
        #             for k, v in d.items():
        #                 stack.append((v, get_topic(sanitized_topic, k), depth + 1))
        #         elif isinstance(d, list):
        #             for i, v in enumerate(d):
        #                 stack.append((v, get_topic(sanitized_topic, str(i)), depth + 1))
        #         else:
        #             # Primitive value
        #             try:
        #                 payload = {"val": d, "ts": 0, "src": "json-tree-sync"}
        #                 mqtt_publisher_service.publish_payload(sanitized_topic, orjson.dumps(payload).decode())
        #             except Exception:
        #                 pass
        # 
        #     if LOCAL_DEBUG: logger.success(f"🌳✅ MQTT Sync Complete for {label}")

        def load_json_data(source):
            if BUILDER_DEBUG: builder_logger.info(f"🚀📑🔄 [DATA] Loading JSON tree data for '{label}'")
            data = None
            if isinstance(source, str):
                try:
                    p = Path(source)
                    if not p.is_absolute():
                        project_root = Path(__file__).parents[3]
                        resolved_p = project_root / source
                    else:
                        resolved_p = p
                    
                    if resolved_p.exists() and resolved_p.is_file():
                        if BUILDER_DEBUG: builder_logger.debug(f"📂🆗✅ [DATA] Loading from file: {resolved_p}")
                        state["source_path"] = resolved_p
                        with open(resolved_p, "rb") as f:
                            data = orjson.loads(f.read())
                    elif source.strip().startswith(("{", "[")):
                        if BUILDER_DEBUG: builder_logger.debug("📝🆗✅ [DATA] Loading from raw JSON string.")
                        data = orjson.loads(source)
                    else:
                        error_msg = f"File not found: {source}"
                        if BUILDER_DEBUG: builder_logger.error(f"🌳❌🚫 [ERROR] {error_msg}")
                        data = {"Error": error_msg}
                except Exception as e:
                    if BUILDER_DEBUG:
                        builder_logger.exception(f"❌🚫🛑 [ERROR] Error loading JSON tree source '{source}'")
                    data = {"Error": str(e)}
            elif isinstance(source, (dict, list)):
                if BUILDER_DEBUG: builder_logger.debug("📦🆗✅ [DATA] Loading from provided dictionary/list object.")
                data = source
            
            state["raw_data"] = data
            
            # Reset Columns if show_values is enabled
            if show_values_var.get():
                if BUILDER_DEBUG: builder_logger.trace(f"📐🔀🔳 [VIEW] Discovering dynamic columns for table view.")
                discover_columns(data)
                tree["columns"] = ("value",) + tuple(state["dynamic_columns"])
                for col in state["dynamic_columns"]:
                    tree.heading(col, text=col.replace("_", " ").title(), anchor="w")
                    tree.column(col, width=150, minwidth=50, stretch=tk.YES)
            else:
                tree["columns"] = ("value",)
                # Ensure headers are restored
                tree.heading("#0", text="Key / Index", anchor="w")
                tree.heading("value", text="Value", anchor="w")

            refresh_tree_display(filter_var.get() if allow_filter else "")
            
            # Auto-Sync to MQTT if enabled
            # if allow_mqtt_sync:
            #     sync_to_mqtt()

        def save_as_json_data():
            if state["raw_data"] is None:
                if BUILDER_DEBUG: builder_logger.error("🌳❌🚫 [ERROR] Cannot save: No data to save.")
                return
            
            filename = filedialog.asksaveasfilename(
                title="Save JSON As",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                try:
                    with open(filename, "wb") as f:
                        f.write(orjson.dumps(state["raw_data"], option=orjson.OPT_INDENT_2))
                    if BUILDER_DEBUG: builder_logger.success(f"🌳✅💾 [SUCCESS] Successfully saved JSON to {filename}")
                    state["source_path"] = Path(filename)
                except Exception as e:
                    if BUILDER_DEBUG:
                        builder_logger.exception(f"❌🚫🛑 [ERROR] Error saving JSON to '{filename}'")

        def browse_file():
            if BUILDER_DEBUG: builder_logger.info("🖱️📂🔍 [INPUT] User browsing for JSON file.")
            filename = filedialog.askopenfilename(
                title="Select JSON File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                load_json_data(filename)

        if allow_browse:
            browse_btn = ttk.Button(header_frame, text="Browse...", command=browse_file)
            browse_btn.pack(side=tk.RIGHT, padx=2)

        if allow_save_as:
            save_as_btn = ttk.Button(footer_frame, text="Save As...", command=save_as_json_data)
            save_as_btn.pack(side=tk.LEFT, padx=2)

        # if allow_mqtt_sync:
        #     sync_btn = ttk.Button(footer_frame, text="Sync to MQTT", command=sync_to_mqtt)
        #     sync_btn.pack(side=tk.LEFT, padx=2)

        # 4. Editing Functionality
        if allow_edit:
            def on_double_click(event):
                item_id = tree.identify_row(event.y)
                column_id = tree.identify_column(event.x)
                if not item_id: return
                
                # RESTRICTION: Only allow editing the 'value' column (column #1)
                # This ensures editing happens 'in the tree' (leaf values) and not in dynamic table columns.
                col_idx = int(column_id.replace("#", ""))
                if col_idx != 1: 
                    return 
                
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆📝 [INPUT] Inline editing started for JSON node: {item_id}")
                logical_col = "value"
                old_value = tree.set(item_id, logical_col)
                x, y, w, h = tree.bbox(item_id, column_id)
                
                entry = ttk.Entry(tree)
                entry.insert(0, old_value)
                entry.select_range(0, tk.END)
                entry.focus_set()
                entry.place(x=x, y=y, width=w, height=h)
                
                def save_edit(event=None):
                    new_value = entry.get()
                    if BUILDER_DEBUG: builder_logger.debug(f"⌨️🔢🆗 [INPUT] Saving JSON node edit: {new_value}")
                    typed_value = new_value
                    if new_value.lower() == "true": typed_value = True
                    elif new_value.lower() == "false": typed_value = False
                    else:
                        try:
                            if "." in new_value: typed_value = float(new_value)
                            else: typed_value = int(new_value)
                        except ValueError: pass
                    
                    tree.set(item_id, logical_col, str(typed_value))
                    update_raw_data(item_id, typed_value)
                    entry.destroy()

                def cancel_edit(event=None):
                    if BUILDER_DEBUG: builder_logger.trace("❌🧹⌨️ [INPUT] Edit cancelled.")
                    entry.destroy()

                entry.bind("<Return>", save_edit)
                entry.bind("<FocusOut>", save_edit)
                entry.bind("<Escape>", cancel_edit)

            def update_raw_data(item_id, new_value):
                # Iterative path reconstruction
                path = []
                curr = item_id
                while curr:
                    text = tree.item(curr, "text")
                    if text.startswith("[") and text.endswith("]"):
                        try: path.insert(0, int(text[1:-1]))
                        except: path.insert(0, text)
                    else:
                        path.insert(0, text)
                    curr = tree.parent(curr)
                
                if not path:
                    state["raw_data"] = new_value
                    return

                d = state["raw_data"]
                try:
                    for i in range(len(path) - 1):
                        d = d[path[i]]
                    
                    d[path[-1]] = new_value
                    
                except (KeyError, IndexError, TypeError) as e:
                    if BUILDER_DEBUG: builder_logger.error(f"🌳❌🚫 [ERROR] Error updating internal data: {e}")

            tree.bind("<Double-1>", on_double_click)

        if json_source:
            load_json_data(json_source)

        if widget_path and state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering JSON tree at path '{widget_path}'")
            # We don't have a single variable, but we register the path for path context
            state_mirror_engine.register_widget(widget_path, None, base_mqtt_topic_from_path, config_data)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing tree state from cache/broker for '{widget_path}'")
            state_mirror_engine.initialize_widget_state(widget_path)

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🗂️ [SUCCESS] The Data JSON Tree '{label}' has materialized!")
        return frame

    # Static method used by the Registry for updates
    @staticmethod
    def _refresh_tree(builder_instance, *args, **kwargs):
        pass
