# builder_audio/dynamic_gui_create_dial.py
#
# A Tkinter Canvas-based 360-degree Dial that respects the global theme.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk
import math
from managers.configini.config_reader import Config

app_constants = Config.get_instance()
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
import os


class CustomDialFrame(ttk.Frame):
    """
    A custom Tkinter Frame that hosts the dial and provides the "Flux Control" methods.
    """

    # Initializes the CustomDialFrame.
    # This sets up the frame that contains the dial widget and binds it to a tkinter
    # variable and state management engine.
    # Inputs:
    #     parent: The parent tkinter widget.
    #     variable (tk.DoubleVar): The variable to store the dial's value.
    #     reff_point (float): A reference point for quick-jump functionality.
    #     path (str): The widget's unique identifier path.
    #     state_mirror_engine: The engine for MQTT state synchronization.
    #     command (function): The callback for when the value changes.
    # Outputs:
    #     None.
    def __init__(
        self,
        parent,
        variable,
        reff_point,
        path,
        state_mirror_engine,
        command,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.variable = variable
        self.min_val = 0
        self.max_val = 999
        self.reff_point = reff_point
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.command = (
            command  # The function to call when value changes (e.g., on_drag_or_click)
        )
        self.temp_entry = None  # Initialize temp_entry

    # Sets the dial's value to its predefined reference point.
    # This provides a quick way to reset the dial to a default or common value.
    # Inputs:
    #     event: The tkinter event object.
    # Outputs:
    #     None.
    def _jump_to_reff_point(self, event):
        """
        ⚡  Jumping to the Reference Point immediately!
        """
        if app_constants.global_settings[
            "debug_enabled"
        ]:  # Use global_settings for consistency
            debug_logger(
                message=f"⚡ User invoked Quantum Jump! Resetting to {self.reff_point}",
                **_get_log_args(),
            )

        self.variable.set(self.reff_point)
        # Directly trigger MQTT update
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    # Opens a temporary entry widget for manual value input.
    # This allows for precise value entry, bypassing direct mouse interaction.
    # Inputs:
    #     event: The tkinter event object, used for positioning the entry widget.
    # Outputs:
    #     None.
    def _open_manual_entry(self, event):
        """
        📝 User requested manual coordinate entry.
        """
        # Ensure only one entry is open at a time
        if self.temp_entry and self.temp_entry.winfo_exists():
            return

        self.temp_entry = tk.Entry(self, width=8, justify="center")

        # Place it exactly where the user clicked (or centered)
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)

        # 3. Insert current value
        current_val = self.variable.get()
        self.temp_entry.insert(0, str(current_val))
        self.temp_entry.select_range(0, tk.END)  # Select all text for easy overwriting

        # 4. Focus so user can type immediately
        self.temp_entry.focus_set()

        # 5. Bind Exit Events (Enter key or Clicking away)
        self.temp_entry.bind("<Return>", self._submit_manual_entry)
        self.temp_entry.bind("<FocusOut>", self._submit_manual_entry)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    # Submits the value from the manual entry widget.
    # This validates the entered value and updates the dial's state if it is within bounds.
    # Inputs:
    #     event: The tkinter event object.
    # Outputs:
    #     None.
    def _submit_manual_entry(self, event):
        """
        Validates the input and sets the new timeline.
        """
        raw_value = self.temp_entry.get()

        try:
            # Validate Number
            new_value = float(raw_value)

            # Check Limits (The laws of physics!)
            if self.min_val <= new_value <= self.max_val:
                # Valid! Set it!
                self.variable.set(new_value)
                # Directly trigger MQTT update.
                if self.state_mirror_engine:
                    self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"✅ Manual entry successful: {new_value}",
                        **_get_log_args(),
                    )
            else:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Value {new_value} out of bounds! Ignoring.",
                        **_get_log_args(),
                    )

        except ValueError:
            # Not a number
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Invalid manual entry: '{raw_value}' is not a number.",
                    **_get_log_args(),
                )

        # Cleanup
        self._destroy_manual_entry(event)

    # Destroys the temporary manual entry widget.
    # Inputs:
    #     event: The tkinter event object.
    # Outputs:
    #     None.
    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None  # Clean up the attribute


class DialCreatorMixin:
    # Creates a custom rotary dial widget.
    # This method handles the creation of the dial, including its visual appearance,
    # user interaction (drag, click), and integration with the state management system.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the dial.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     CustomDialFrame: The created dial frame widget, or None on failure.
    def _create_dial(self, parent_widget, config_data, **kwargs):  # Updated signature
        """Creates a rotary dial widget."""
        current_function_name = "_create_dial"

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to forge a themed dial for '{label}'.",
                **_get_log_args(),
            )

        # Resolve Theme Colors
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")

        # 1. Extract the Custom Color (Default to the theme's accent color if missing)
        # We look for 'indicator_color' in the JSON config
        indicator_color = config.get("indicator_color", accent_color)

        # Create our custom frame type
        min_val = 0
        max_val = 999
        reff_point = float(
            config.get("reff_point", (min_val + max_val) / 2.0)
        )  # Default reff_point to midpoint
        value_default = float(config.get("value_default", 0.0))  # Ensure float

        dial_value_var = tk.DoubleVar(value=value_default)

        drag_state = {"start_y": None, "start_value": None}

        def on_dial_press(event):
            """Stores the starting Y-position and value when the dial is clicked."""
            drag_state["start_y"] = event.y
            drag_state["start_value"] = dial_value_var.get()

        def on_dial_drag(event):
            """Calculates the new value based on the vertical distance dragged."""
            if drag_state["start_y"] is None:
                return

            dy = drag_state["start_y"] - event.y
            sensitivity = (max_val - min_val) / 100.0  # Full range over 100 pixels
            new_val = drag_state["start_value"] + (dy * sensitivity)
            
            new_val = max(min_val, min(max_val, new_val))

            if dial_value_var.get() != new_val:
                dial_value_var.set(new_val)
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        def on_dial_release(event):
            """Clears the drag state when the mouse button is released."""
            drag_state["start_y"] = None
            drag_state["start_value"] = None

        frame = CustomDialFrame(
            parent_widget,  # Use parent_widget here
            variable=dial_value_var,
            reff_point=reff_point,
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=None,  # Command is handled by the press/drag/release events now
        )

        show_label = config.get("show_label", True)
        if label and show_label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        try:
            width = config.get("width", 50)
            height = config.get("height", 50)
            piechart = config.get("piechart", True)
            pointer = config.get("pointer", True)

            # Canvas with Theme Background
            canvas = tk.Canvas(
                frame, width=width, height=height, bg=bg_color, highlightthickness=0
            )
            canvas.pack()

            # Value Label (initially based on default value var)
            value_label = ttk.Label(
                frame, text=f"{int(dial_value_var.get())}", font=("Helvetica", 8)
            )
            value_label.pack(side=tk.BOTTOM)

            def update_dial_visuals(
                *args,
                neutral_color_val=fg_color,
                accent_for_arc_val=accent_color,
                indicator_color_val=indicator_color,
                secondary_val=secondary_color,
            ):
                current_dial_val = dial_value_var.get()
                value_label.config(text=f"{int(current_dial_val)}")
                self._draw_dial(
                    canvas,
                    width,
                    height,
                    current_dial_val,
                    frame.min_val,
                    frame.max_val,
                    value_label,
                    neutral_color_val,
                    accent_for_arc_val,
                    indicator_color_val,
                    secondary_val,
                    piechart=piechart,
                    pointer=pointer
                )
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚡ fluxing... Dial '{label}' updated visually to {current_dial_val} from MQTT.",
                        **_get_log_args(),
                    )

            dial_value_var.trace_add("write", update_dial_visuals)

            # Initial draw based on default value
            update_dial_visuals()

            # Drag Interaction
            canvas.bind("<Button-1>", on_dial_press)
            canvas.bind("<B1-Motion>", on_dial_drag)
            canvas.bind("<ButtonRelease-1>", on_dial_release)

            # --- Bind Special Keys for Quantum Jump and Precise Entry ---
            canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)

            if path:
                self.topic_widgets[path] = dial_value_var
                widget_id = path
                state_mirror_engine.register_widget(widget_id, dial_value_var, base_mqtt_topic_from_path, config_data)
                
                from workers.handlers.widget_event_binder import bind_variable_trace
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
                bind_variable_trace(dial_value_var, callback)
                
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The themed dial '{label}' is calibrated!",
                    **_get_log_args(),
                )
            return frame

        except Exception as e:
            debug_logger(message=f"❌ The dial '{label}' shattered! Error: {e}")
            return None

    # Draws the rotary dial widget on the canvas.
    # This method is responsible for all the visual elements of the dial, including the
    # background track, the active value arc, and the pointer line.
    # Inputs:
    #     canvas: The tkinter canvas to draw on.
    #     width, height (int): The dimensions of the canvas.
    #     value (float): The current value of the dial.
    #     min_val, max_val (float): The min/max values of the dial (0-999).
    #     value_label (ttk.Label): The label for displaying the current value.
    #     neutral_color, accent_for_arc, indicator_color, secondary (str): Color values from the theme.
    #     piechart (bool): Whether to draw the pie slice fill.
    #     pointer (bool): Whether to draw the pointer line.
    # Outputs:
    #     None.
    def _draw_dial(
        self,
        canvas,
        width,
        height,
        value,
        min_val,
        max_val,
        value_label,
        neutral_color,
        accent_for_arc,
        indicator_color,
        secondary,
        piechart=True,
        pointer=True
    ):
        canvas.delete("all")
        cx, cy = width / 2, height / 2
        radius = min(width, height) / 2 - 5

        # 1. Background Arc (The Track) - Full 360 degrees
        canvas.create_arc(
            5,
            5,
            width - 5,
            height - 5,
            start=0,
            extent=359.9,
            style=tk.ARC,
            outline=secondary,
            width=4,
        )

        # 2. Calculate Normalized Value (0.0 to 1.0)
        norm_val = (value - min_val) / (max_val - min_val) if max_val > min_val else 0

        # 3. Active Arc (Pie Chart)
        start_angle = 90  # Start from the top
        val_extent = -360 * norm_val # Negative for clockwise
        active_color = indicator_color
        
        if piechart:
            canvas.create_arc(
                5,
                5,
                width - 5,
                height - 5,
                start=start_angle,
                extent=val_extent,
                style=tk.PIESLICE,
                fill=active_color,
                outline=active_color,
                width=1,
            )

        # 4. The Pointer Line
        if pointer:
            angle_rad = math.radians(start_angle + val_extent)
            px = cx + radius * math.cos(angle_rad)
            py = cy - radius * math.sin(angle_rad)  # Canvas Y is inverted
            canvas.create_line(
                cx, cy, px, py, fill=indicator_color, width=3, capstyle=tk.ROUND
            )
        
        value_label.config(foreground=active_color)