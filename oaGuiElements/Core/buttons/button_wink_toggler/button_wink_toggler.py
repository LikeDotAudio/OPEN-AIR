# button_wink_toggler/button_wink_toggler.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from tkinter import ttk

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiElements.Core.buttons.button_wink.button_wink import BuilderButtonWinkCreator


class BuilderButtonWinkTogglerCreator(BuilderButtonWinkCreator):
    """A mixin to create a radio-group of Wink buttons."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderButtonWinkTogglerCreator.build(parent_widget, config_data, context, **kwargs)

    def make_button_wink_toggler(self, parent_widget, config_data, context=None, **kwargs):
        """Legacy compatibility wrapper."""
        return self.build(parent_widget, config_data, context, **kwargs)

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Creates a group of Wink buttons where only one can be active."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️🔘 [BUILDER] Entering _assemble_ui", level="TRACE")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")
    
        # Extract config
        label = get_text(get_text(config_data.get('label_active'))) or get_text(get_text(config_data.get('label')), "")
        config = config_data
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...", level="TRACE")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.", level="DEBUG")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            app_instance = kwargs.get("app_instance")
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.", level="DEBUG")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️🔘 [BUILDER] Spawning wink toggler group for '{label}' at path '{path}'.", level="DEBUG")

        # 1. Root Container (Use Canvas for transparency)
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🪟🎨 [CONSTRUCT] Creating main canvas container for wink toggler '{label}'", level="TRACE")
        container = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat")
        if hasattr(builder_instance, '_apply_transparency'):
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"👻🌀🪟 [ALPHA] Applying industrial transparency to toggler container '{label}'", level="TRACE")
            builder_instance._apply_transparency(container, container, config, builder_instance)
        
        # 2. Group Frame (standard tk.Frame since container canvas handles the main bg)
        # Note: We use tk.Frame with bg="" or matching to ensure transparency mixin can handle it if needed
        group_frame = tk.Frame(container, bd=0, highlightthickness=0, relief="flat")
        
        # Add top padding if there is a label to avoid overlap
        pady_top = 25 if label else 0
        group_frame.pack(fill="both", expand=True, pady=(pady_top, 0))

        # Make group_frame transparent too if it's on a canvas
        if hasattr(builder_instance, '_apply_transparency'):
            builder_instance._apply_transparency(group_frame, group_frame, config, builder_instance)

        container._last_redraw_size = (0, 0)

        def redraw_group_labels():
            if not container.winfo_exists(): return
            w = container.winfo_width()
            h = container.winfo_height()
            if (w, h) == container._last_redraw_size:
                return
            if w <= 1: return
            container._last_redraw_size = (w, h)
            
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄🎨🔤 [REDRAW] Redrawing labels for wink toggler '{label}'", level="TRACE")
            container.delete("industrial_text")
            if label:
                container.create_text(
                    10, 12, text=label, anchor="w",
                    fill="white", font=("TkDefaultFont", 10, "bold"),
                    tags="industrial_text"
                )

        def sync_bg():
            redraw_group_labels()
            # Background cache might need a kick
            if hasattr(builder_instance, '_apply_transparency'):
                builder_instance._apply_transparency(container, container, config, builder_instance)
        
        container._draw = sync_bg
        container.render = sync_bg
        container.bind("<Configure>", lambda e: redraw_group_labels(), add="+")

        options = config.get("options", {})
        
        # Normalize options to dict if list
        if isinstance(options, list):
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚠️🔔🔡 [CONFIG] Options for wink toggler '{label}' is a list, converting to dict.", level="DEBUG")
            options_dict = {}
            for item in options:
                options_dict[item] = {"label_active": str(item)}
            options = options_dict

        # Default Value
        value_default = config.get(
            "value_default", next(iter(options.keys())) if options else None
        )
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔋🔘✨ [STATE] Initial selected wink key for '{label}': {value_default}", level="DEBUG")
        
        layout_columns = int(config.get("layout_columns", 1))
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📐📏🔳 [LAYOUT] Columns: {layout_columns}", level="DEBUG")

        # Main Group Variable (Strings for Radio behavior)
        group_var = kwargs.get("variable") or tk.StringVar(master=parent_widget, value=value_default)
        
        # Store refs to keep them alive
        self._toggle_refs = getattr(self, "_toggle_refs", [])
        self._toggle_refs.append(group_var)

        row, col = 0, 0
        
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🔳🕹️ [CONSTRUCT] Iterating through options to create Wink buttons for '{label}' group.", level="TRACE")
        for key, button_config in options.items():
            
            # Merge configs: Parent config is base, button_config overrides
            full_config = config.copy()
            full_config.update(button_config)
            
            if path:
                full_config["path"] = f"{path}/{key}"
            
            # Create the BooleanVar for this button
            bool_var = tk.BooleanVar(master=parent_widget, value=(str(value_default) == str(key)))
            
            # ... sync logic ...
            def sync_from_group(var_name, index, mode, k=key, bv=bool_var):
                is_selected = (group_var.get() == str(k))
                if bv.get() != is_selected:
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄✨🔘 [SYNC] Syncing wink '{k}' from group variable: {is_selected}", level="TRACE")
                    bv.set(is_selected)
            group_var.trace_add("write", sync_from_group)
            
            def sync_from_bool(var_name, index, mode, k=key, bv=bool_var):
                if bv.get():
                    if group_var.get() != str(k):
                        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚡🔄🔋 [STATE] Wink '{k}' selected. Updating group variable.", level="DEBUG")
                        group_var.set(k)
            bool_var.trace_add("write", sync_from_bool)

            # Create the button container (Directly call create button on group_frame)
            # To fix the "border" issue, we ensure each button gets its own transparency check
            btn_cell = tk.Frame(group_frame, bd=0, highlightthickness=0, relief="flat")
            btn_cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            if hasattr(builder_instance, '_apply_transparency'):
                builder_instance._apply_transparency(btn_cell, btn_cell, full_config, builder_instance)
            
            # Create Button Widget
            full_config["latching"] = True 
            widget = BuilderButtonWinkCreator.make(btn_cell, full_config, context=context, variable=bool_var, builder_instance=builder_instance)
            widget.pack(fill="both", expand=True)

            # Ensure child container respects parent's background
            def sync_child_bg(wid=widget):
                if hasattr(wid, "_draw"):
                    wid._draw()
            
            if not hasattr(container, "_sync_list"):
                container._sync_list = []
            container._sync_list.append(sync_child_bg)
            
            col += 1
            if col >= layout_columns:
                col = 0
                row += 1

        # Chain all syncs into container._draw
        old_draw = container._draw
        def composite_draw():
            if old_draw: old_draw()
            for s in container._sync_list:
                s()
        container._draw = composite_draw

        # --- MQTT for the Group ---
        if path and state_mirror_engine:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔗 [MQTT] Registering wink toggler group at path '{path}'", level="TRACE")
            widget_id = path
            topic = state_mirror_engine.register_widget(
                widget_id, group_var, base_mqtt_topic_from_path, config
            )
            
            if subscriber_router and topic:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Subscribing to group topic: {topic}", level="DEBUG")
                subscriber_router.subscribe_to_topic(
                    topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                )
            
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄⏳🔋 [STATE] Initializing group state from cache/broker for '{path}'", level="TRACE")
            state_mirror_engine.initialize_widget_state(path)

        redraw_group_labels()
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗🔘 [SUCCESS] The wink toggler group '{label}' has materialized!", level="SUCCESS")
        return container, container
