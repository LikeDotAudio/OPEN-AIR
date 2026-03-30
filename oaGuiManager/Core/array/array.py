# array/array.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
import orjson
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiManager.Core.context.widget_context import WidgetContext

class ViewManager:
    def __init__(self, root_widget):
        self.groups = {}  # { "aux1": [widget_instance, ...] }
        self.states = {}  # { "aux1": "expanded" }
        self.vars = {}    # { "aux1": tk.BooleanVar }
        self.menu = tk.Menu(root_widget, tearoff=0)
        self.root = root_widget

    def register(self, group_name, widget):
        if group_name not in self.groups:
            self.groups[group_name] = []
            self.states[group_name] = "expanded"
            
            # Create BooleanVar for menu
            var = tk.BooleanVar(value=True)
            self.vars[group_name] = var
            
            # Add to menu
            self.menu.add_checkbutton(
                label=f"Show {group_name}",
                variable=var,
                command=lambda g=group_name: self._on_menu_click(g)
            )
            
        self.groups[group_name].append(widget)

    def _on_menu_click(self, group_name):
        # Toggle state based on var
        is_checked = self.vars[group_name].get()
        new_state = "expanded" if is_checked else "collapsed"
        self.set_state(group_name, new_state)

    def set_state(self, group_name, state):
        self.states[group_name] = state
        
        # Update var if changed programmatically
        if group_name in self.vars:
            self.vars[group_name].set(state == "expanded")

        widgets = self.groups.get(group_name, [])
        for w in widgets:
            if hasattr(w, "set_view_state"):
                w.set_view_state(state)

    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

class BuilderArrayCreator(TransparencyMixin):
    @staticmethod
    def make(parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """Standardized factory entry point."""
        # Use existing instance if passed, otherwise create creator instance
        builder_inst = context.builder_instance if context else kwargs.get("builder_instance")
        return BuilderArrayCreator().make_array(parent_widget, config_data, context=context, **kwargs)

    def make_array(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        if LOCAL_DEBUG: logger.trace(f"🔬 Entering make_array with config: {config_data}")
        """
        Generates a grid of widgets based on a blueprint and a data array.
        Supports collapsible rows (OcaCollapsibleBlock) managed by a ViewManager.
        """
        # ⚡ HARDENED INTERFACE: Extract from context if available
        on_complete = context.on_complete if context else kwargs.get("on_complete")
        builder_instance = context.builder_instance if context else kwargs.get("builder_instance")
        
        # Fallback to self if no builder provided (unlikely in normal flow)
        if not builder_instance:
            builder_instance = self

        # 1. Main Container
        p_bg = "#2b2b2b"
        try: p_bg = parent_widget.cget("bg")
        except: pass
        main_container = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", bg=p_bg)
        
        # ⚡ DIMENSION ENFORCEMENT: Ensure main container respects explicit sizes
        geom = config_data.get("geometry", {})
        w = config_data.get("width") or geom.get("width")
        h = config_data.get("height") or geom.get("height")
        if w or h:
            main_container.grid_propagate(False)
            main_container.pack_propagate(False)
            if w: main_container.config(width=w)
            if h: main_container.config(height=h)

        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(main_container, main_container, config_data, builder_instance)

        # 2. Initialize ViewManager attached to this container
        view_manager = ViewManager(main_container)
        
        # Bind Right-Click to Main Container
        main_container.bind("<Button-3>", view_manager.show_menu)

        # 3. Content Grid Container
        grid_container = tk.Canvas(main_container, bd=0, highlightthickness=0, relief="flat")
        grid_container.grid(row=0, column=0, sticky="nsew")

        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(grid_container, grid_container, config_data, builder_instance)
        
        # Bind Right-Click to Grid Container as well
        grid_container.bind("<Button-3>", view_manager.show_menu)

        # Get Data and Blueprint
        blueprint = config_data.get("blueprint", {})
        data_array = config_data.get("data", [])
        layout_cols = config_data.get("layout_columns", 8)
        
        # ⚡ COMPOSITION FIX: Ensure we use an instance of this creator for internal helpers
        # because 'self' when called via factory wrapper is actually the DynamicGuiBuilder.
        creator_instance = BuilderArrayCreator()

        # Configure Grid Container Columns
        column_sizing = config_data.get("column_sizing", [])
        for col_idx in range(layout_cols):
            sizing_info = column_sizing[col_idx] if col_idx < len(column_sizing) else {}
            weight = sizing_info.get("weight", 1)
            minwidth = sizing_info.get("minwidth", 0)
            maxwidth = sizing_info.get("maxwidth", 0)
            
            # ⚡ OPTIMIZATION: If maxwidth is specified, enforce it by clamping minsize 
            # and disabling expansion (weight=0) if it's meant to be a fixed/max column.
            if maxwidth > 0:
                minwidth = maxwidth
                weight = 0

            grid_container.grid_columnconfigure(col_idx, weight=weight, minsize=minwidth)

        # 5. Construct fields and Inject Data
        synthetic_fields = {}
        
        # ⚡ OPTIMIZATION: Use orjson for deep copy of blueprint
        blueprint_json = orjson.dumps(blueprint).decode()

        if LOCAL_DEBUG: logger.debug(f"🧱 ArrayCreator: Expanding blueprint for {len(data_array)} elements in {config_data.get('path', 'root')}")

        for idx, item in enumerate(data_array):
            item_id = item.get("id", f"item_{idx}")
            if LOCAL_DEBUG: logger.trace(f"  └─ 💠 Processing Array Element [{idx}]: ID='{item_id}'")
            
            try:
                item_config = orjson.loads(blueprint_json)
            except Exception as e:
                logger.error(f"  └─ ❌ FAILED to deep-copy blueprint for element {idx}: {e}")
                continue
            
            # Inject generic data
            if LOCAL_DEBUG: logger.trace(f"    ├─ 💉 Injecting data contexts into element '{item_id}'")
            creator_instance._inject_data(item_config, item)
            
            # Pass ViewManager reference via a special key
            creator_instance._inject_view_manager(item_config, view_manager)

            synthetic_fields[str(item_id)] = item_config
            if LOCAL_DEBUG: logger.trace(f"    └─ ✅ Element '{item_id}' ready for batch build.")

        # 6. Create configuration for batch builder
        container_config = {
            "type": "OcaBlock", 
            "layout_columns": layout_cols,
            "column_sizing": config_data.get("column_sizing", []),
            "fields": synthetic_fields,
            "show_label": False,
            "layout": config_data.get("layout", {}) 
        }
        
        current_path = config_data.get("path", "")
        if LOCAL_DEBUG: logger.debug(f"🚀 ArrayCreator: Handing off synthetic container '{current_path}' to BatchBuilder...")
        builder_instance._create_dynamic_widgets(
            grid_container, container_config, 
            path_prefix=current_path, 
            on_complete=on_complete,
            context=context
        )
        
        return main_container

    def _inject_data(self, config, data_context):
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    self._inject_data(value, data_context)
                elif isinstance(value, str) and "{{" in value:
                    config[key] = self._resolve_placeholder(value, data_context)
        elif isinstance(config, list):
            for i, value in enumerate(config):
                if isinstance(value, (dict, list)):
                    self._inject_data(value, data_context)
                elif isinstance(value, str) and "{{" in value:
                    config[i] = self._resolve_placeholder(value, data_context)
    
    def _inject_view_manager(self, config, manager):
        """Recursively inject _view_manager into OcaCollapsibleBlocks"""
        if isinstance(config, dict):
            if config.get("type") == "OcaCollapsibleBlock":
                config["_view_manager"] = manager
            for value in config.values():
                self._inject_view_manager(value, manager)

    def _resolve_placeholder(self, value, data_context):
        for data_key, data_val in data_context.items():
            placeholder = f"{{{{{data_key}}}}}"
            if value == placeholder:
                return data_val
            if placeholder in value:
                value = value.replace(placeholder, str(data_val))
        return value
