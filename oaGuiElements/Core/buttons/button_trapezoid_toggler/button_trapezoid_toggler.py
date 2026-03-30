# button_trapezoid_toggler/button_trapezoid_toggler.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: button_trapezoid_toggler/trapezoid_toggler.py

import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiElements.Core.buttons.button_trapezoid.button_trapezoid import BuilderButtonTrapezoidCreator


class BuilderButtonTrapezoidTogglerCreator(BuilderButtonTrapezoidCreator):
    """A mixin to create a radio-group of trapezoid buttons."""

    # Creates a group of trapezoid buttons that function as a radio group.
    # This method arranges multiple trapezoid buttons where only one can be active at a time.
    # It manages the group's state and connects it to the state management engine.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the button group.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Canvas: The created container canvas for the button group.
    def make_button_trapezoid_toggler(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
        """Creates a group of trapezoid buttons where only one can be active."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🔳 [BUILDER] Entering make_button_trapezoid_toggler")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        # Extract widget-specific config from config_data
        label = config_data.get("label_active") or config_data.get("label", "")
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

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🔳 [BUILDER] Spawning trapezoid toggler group for '{label}' at path '{path}'.")

        # 1. Root Container (Use Canvas for transparency)
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating main canvas container for trapezoid toggler '{label}'")
        container = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat")
        if hasattr(self, '_apply_transparency'):
            # ⚡ Force transparency for the group container
            trans_config = config.copy()
            if "bg_color" not in trans_config: trans_config["transparent"] = True
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to toggler container '{label}'")
            self._apply_transparency(container, container, trans_config, builder_instance)

        # 2. Group Frame (Use Canvas for transparency)
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating internal group frame canvas for '{label}'")
        group_frame = tk.Canvas(container, bd=0, highlightthickness=0, relief="flat")
        if hasattr(self, '_apply_transparency'):
            # ⚡ Force transparency for the group frame
            trans_config = config.copy()
            if "bg_color" not in trans_config: trans_config["transparent"] = True
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to internal group frame '{label}'")
            self._apply_transparency(group_frame, group_frame, trans_config, builder_instance)
            
        # Add top padding if there is a label to avoid overlap
        pady_top = 25 if label else 0
        group_frame.pack(fill="both", expand=True, pady=(pady_top, 0))

        container._last_redraw_size = (0, 0)

        def redraw_group_labels():
            if not container.winfo_exists(): return
            w = container.winfo_width()
            h = container.winfo_height()
            
            if (w, h) == container._last_redraw_size:
                return
            
            if w <= 1: return
            container._last_redraw_size = (w, h)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄🎨🔤 [REDRAW] Redrawing labels for trapezoid toggler '{label}'")
            container.delete("industrial_text")
            if label:
                container.create_text(
                    10, 12, text=label, anchor="w",
                    fill="white", font=("TkDefaultFont", 10, "bold"),
                    tags="industrial_text"
                )

        def sync_bg():
            redraw_group_labels()
            # Redraw child buttons - each button is its own canvas now
            for b_info in buttons.values():
                if hasattr(b_info["canvas"], "_draw"):
                    b_info["canvas"]._draw()
        
        container._draw = sync_bg
        container.render = sync_bg
        container.bind("<Configure>", lambda e: redraw_group_labels(), add="+")

        options = config.get("options", {})
        
        # Handle list format for options (convert to dict)
        if isinstance(options, list):
            if BUILDER_DEBUG: builder_logger.debug(f"⚠️🔔🔡 [CONFIG] Options for trapezoid toggler '{label}' is a list, converting to dict.")
            options_dict = {}
            for item in options:
                options_dict[item] = {"label_active": str(item)}
            options = options_dict

        value_default = config.get(
            "value_default", next(iter(options.keys())) if options else None
        )
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🔘✨ [STATE] Initial selected trapezoid key for '{label}': {value_default}")
        
        layout_columns = int(config.get("layout_columns", 4))
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔳 [LAYOUT] Grid columns: {layout_columns}")

        selected_var = kwargs.get("variable") or tk.StringVar(master=parent_widget, value=value_default)
        buttons = {}

        # --- MQTT and State Mirroring ---
        def on_state_change(*args):
            """Called when selected_var changes, triggers redraw and MQTT broadcast."""
            if BUILDER_DEBUG: builder_logger.info(f"⚡🔄🔋 [STATE] Trapezoid toggler '{label}' state change: {selected_var.get()}")
            for key, button_info in buttons.items():
                # The individual buttons listen to selected_var indirectly 
                # (via their own redraw which uses selected_var.get())
                if hasattr(button_info["canvas"], "_draw"):
                    button_info["canvas"]._draw()

            if state_mirror_engine:
                if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Broadcasting state change for '{path}'")
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        selected_var.trace_add("write", on_state_change)

        if path and state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering trapezoid toggler at path '{path}'")
            widget_id = path
            topic = state_mirror_engine.register_widget(
                widget_id, selected_var, base_mqtt_topic_from_path, config
            )

            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                subscriber_router.subscribe_to_topic(
                    topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                )

        row, col = 0, 0
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Iterating through options to create trapezoid buttons for '{label}' group.")
        for key, button_config in options.items():
            # Inherit properties from parent config if not specified in button config
            full_config = config.copy()
            full_config.update(button_config)
            
            # Robust Background Inheritance
            try:
                p_bg = group_frame.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except:
                p_bg = "#2b2b2b"
            
            if "bg_color" not in full_config:
                full_config["bg_color"] = p_bg

            # Create the button using the base creator, passing our shared selected_var logic
            # We need a boolean var for each button that reflects if it is selected
            bool_var = tk.BooleanVar(master=parent_widget, value=(selected_var.get() == key))
            
            # Sync shared selected_var -> individual bool_var
            def sync_to_bool(v, i, m, k=key, bv=bool_var):
                bv.set(selected_var.get() == str(k))
            selected_var.trace_add("write", sync_to_bool)

            # Create the button widget (it will be its own canvas)
            # We don't want the button to have its own path registration yet, 
            # or maybe we do if it's a multi-path setup. 
            # But usually toggler is one path.
            # Base creator will register if path is in full_config.
            btn_canvas = BuilderButtonTrapezoidCreator.make(
                group_frame, full_config, variable=bool_var, 
                context=context, # ⚡ MANDATORY: Pass context for transparency!
                base_mqtt_topic_from_path=base_mqtt_topic_from_path
            )
            btn_canvas.grid(row=row, column=col, padx=5, pady=5)

            buttons[key] = {
                "canvas": btn_canvas,
                "config": full_config,
                "state": {"lit": bool_var.get()} # placeholder
            }

            # Override the click behavior to update the shared selected_var
            def on_btn_release(event, k=key):
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆🔳 [INPUT] Toggler '{label}' member release: '{k}'")
                selected_var.set(k)

            btn_canvas.bind("<ButtonRelease-1>", on_btn_release, add="+")

            col += 1
            if col >= layout_columns:
                col = 0
                row += 1

        # Initialize state from cache or broadcast the initial state
        if path and state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'")
            state_mirror_engine.initialize_widget_state(path)

        redraw_group_labels()
        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🔘 [SUCCESS] The trapezoid toggler group '{label}' has materialized!")
        return container

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderButtonTrapezoidTogglerCreator()
        return creator.make_button_trapezoid_toggler(parent_widget, config_data, context, **kwargs)
