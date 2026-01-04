# workers/builder/audio/dynamic_gui_create_trapezoid_toggler.py

import tkinter as tk
from tkinter import ttk
from .dynamic_gui_create_trapezoid_button import TrapezoidButtonCreatorMixin
from managers.configini.config_reader import Config

app_constants = Config.get_instance()
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

class TrapezoidButtonTogglerCreatorMixin(TrapezoidButtonCreatorMixin):
    """A mixin to create a radio-group of trapezoid buttons."""

    def _create_trapezoid_button_toggler(self, parent_frame, label, config, path, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router):
        """Creates a group of trapezoid buttons where only one can be active."""
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(message=f"Creating trapezoid button toggler group: {label}", **_get_log_args())

        container = ttk.Frame(parent_frame)
        
        if label:
            ttk.Label(container, text=label).pack(fill="x", expand=True, pady=(0, 5))
            
        group_frame = ttk.Frame(container)
        group_frame.pack(fill="x", expand=True)

        options = config.get("options", {})
        value_default = config.get("value_default", next(iter(options.keys())) if options else None)
        layout_columns = int(config.get("layout_columns", 4))

        selected_var = tk.StringVar(value=value_default)
        buttons = {}

        # --- MQTT and State Mirroring ---
        def on_state_change(*args):
            """Called when selected_var changes, triggers redraw and MQTT broadcast."""
            for key, button_info in buttons.items():
                is_lit = (selected_var.get() == key)
                button_info["state"]["lit"] = is_lit
                self._draw_trapezoid_button(button_info["canvas"], button_info["config"], button_info["state"])
            
            if state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)
        
        selected_var.trace_add("write", on_state_change)
        
        if path and state_mirror_engine:
            widget_id = path
            state_mirror_engine.register_widget(widget_id, selected_var, base_mqtt_topic_from_path, config)
            
            # Subscribe to the topic for incoming messages
            from workers.mqtt.mqtt_topic_utils import get_topic
            topic = get_topic("OPEN-AIR", base_mqtt_topic_from_path, widget_id)
            subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)

        # Theme Resolution
        from workers.styling.style import THEMES, DEFAULT_THEME
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")

        row, col = 0, 0
        for key, button_config in options.items():
            
            button_frame = ttk.Frame(group_frame)
            button_frame.grid(row=row, column=col, padx=2, pady=2)

            # Inherit properties from parent config if not specified in button config
            full_config = config.copy()
            full_config.update(button_config)

            width = full_config.get("width", 50)
            height = full_config.get("height", 40)
            base_color = full_config.get("color", "#333333")
            led_color = full_config.get("led_color", "#FF0000")

            canvas = tk.Canvas(button_frame, width=width, height=height, bg=bg_color, highlightthickness=0)
            canvas.pack()
            
            # Each button has its own press state, but shares the lit state via the selected_var
            button_state = {
                "pressed": False,
                "lit": (selected_var.get() == key),
                "base_color": base_color,
                "led_color": led_color
            }

            buttons[key] = {
                "canvas": canvas,
                "config": full_config,
                "state": button_state
            }

            def on_press(event, k=key):
                buttons[k]["state"]["pressed"] = True
                self._draw_trapezoid_button(buttons[k]["canvas"], buttons[k]["config"], buttons[k]["state"])

            def on_release(event, k=key):
                buttons[k]["state"]["pressed"] = False
                selected_var.set(k) # This triggers the trace and redraws all buttons
            
            canvas.bind("<Button-1>", on_press)
            canvas.bind("<ButtonRelease-1>", on_release)
            
            # Initial draw for each button
            self._draw_trapezoid_button(canvas, full_config, button_state)

            col += 1
            if col >= layout_columns:
                col = 0
                row += 1

        # Initialize state from cache or broadcast the initial state
        if path and state_mirror_engine:
            state_mirror_engine.initialize_widget_state(path)

        return container