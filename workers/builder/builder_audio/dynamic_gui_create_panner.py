# builder_audio/dynamic_gui_create_panner.py
#
# A Tkinter Canvas-based Panner that respects the global theme.
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


class CustomPannerFrame(ttk.Frame):
    """
    A custom Tkinter Frame that hosts the panner and provides the "Flux Control" methods.
    """

    # Initializes the CustomPannerFrame.
    # This sets up the frame containing the panner widget, binding it to a tkinter variable
    # and the application's state management engine.
    # Inputs:
    #     parent: The parent tkinter widget.
    #     variable (tk.DoubleVar): The variable to store the panner's value.
    #     min_val, max_val (float): The min/max values of the panner.
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
        min_val,
        max_val,
        reff_point,
        path,
        state_mirror_engine,
        command,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.variable = variable
        self.min_val = min_val
        self.max_val = max_val
        self.reff_point = reff_point
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.command = (
            command  # The function to call when value changes (e.g., on_drag_or_click)
        )
        self.temp_entry = None  # Initialize temp_entry

    # Sets the panner's value to its predefined reference point.
    # This provides a quick way to reset the panner to a default or center value.
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
    #     event: The tkinter event object, used for positioning.
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
    # This validates the entered value and updates the panner's state if it is within bounds.
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


class PannerCreatorMixin:
    # Creates a rotary panner widget.
    # This method sets up the panner, including its visual appearance, user interaction,
    # and integration with the state management system.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the panner.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     CustomPannerFrame: The created panner frame widget, or None on failure.
    def _create_panner(self, parent_widget, config_data, **kwargs):  # Updated signature
        """Creates a rotary panner widget."""
        current_function_name = "_create_panner"

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
                message=f"🔬⚡️ Entering '{current_function_name}' to forge a themed panner for '{label}'.",
                **_get_log_args(),
            )

        # Resolve Theme Colors
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")
        # Customization: Allow indicator_color to be specified in config, default to accent_color
        indicator_color = config.get("indicator_color", accent_color)

        # Create our custom frame type
        min_val = float(config.get("min", -100.0))
        max_val = float(config.get("max", 100.0))
        reff_point = float(
            config.get("reff_point", (min_val + max_val) / 2.0)
        )  # Default reff_point to midpoint
        value_default = float(config.get("value_default", 0.0))  # Ensure float

        panner_value_var = tk.DoubleVar(value=value_default)

        drag_state = {"start_y": None, "start_value": None}

        def on_panner_press(event):
            """Stores the starting Y-position and value when the panner is clicked."""
            drag_state["start_y"] = event.y
            drag_state["start_value"] = panner_value_var.get()

        def on_panner_drag(event):
            """Calculates the new value based on the vertical distance dragged."""
            if drag_state["start_y"] is None:
                return

            dy = drag_state["start_y"] - event.y
            sensitivity = (max_val - min_val) / 100.0
            new_val = drag_state["start_value"] + (dy * sensitivity)
            new_val = max(min_val, min(max_val, new_val))

            if panner_value_var.get() != new_val:
                panner_value_var.set(new_val)
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        def on_panner_release(event):
            """Clears the drag state when the mouse button is released."""
            drag_state["start_y"] = None
            drag_state["start_value"] = None

        frame = CustomPannerFrame(
            parent_widget,  # Use parent_widget here
            variable=panner_value_var,
            min_val=min_val,
            max_val=max_val,
            reff_point=reff_point,
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=None,  # Command is handled by the press/drag/release events now
        )
        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        try:
            width = config.get("width", 50)
            height = config.get("height", 50)

            # Canvas with Theme Background
            canvas = tk.Canvas(
                frame, width=width, height=height, bg=bg_color, highlightthickness=0
            )
            canvas.pack()

            # Value Label (initially based on default value var)
            value_label = ttk.Label(
                frame, text=f"{int(panner_value_var.get())}", font=("Helvetica", 8)
            )
            value_label.pack(side=tk.BOTTOM)

            def update_panner_visuals(*args):
                current_panner_val = panner_value_var.get()
                value_label.config(text=f"{int(current_panner_val)}")
                self._draw_panner_visuals(
                    canvas,
                    width,
                    height,
                    current_panner_val,
                    frame.min_val,
                    frame.max_val,
                    value_label,
                    fg_color,
                    accent_color,
                    secondary_color,
                )
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚡ fluxing... Panner '{label}' updated visually to {current_panner_val} from MQTT.",
                        **_get_log_args(),
                    )

            panner_value_var.trace_add("write", update_panner_visuals)

            # Initial draw based on default value
            update_panner_visuals()

            # Drag Interaction
            canvas.bind("<Button-1>", on_panner_press)
            canvas.bind("<B1-Motion>", on_panner_drag)
            canvas.bind("<ButtonRelease-1>", on_panner_release)

            # --- Bind Special Keys for Quantum Jump and Precise Entry ---
            canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)

            # Register the StringVar with the StateMirrorEngine for MQTT updates
            if path:
                widget_id = path
                self.state_mirror_engine.register_widget(
                    widget_id, panner_value_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to the topic for incoming messages
                from workers.mqtt.mqtt_topic_utils import get_topic

                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id)
                self.subscriber_router.subscribe_to_topic(
                    topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (DoubleVar: {panner_value_var.get()}).",
                        **_get_log_args(),
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The themed panner '{label}' is calibrated!",
                    **_get_log_args(),
                )
            return frame

        except Exception as e:
            debug_logger(message=f"❌ The panner '{label}' shattered! Error: {e}")
            return None

    # Draws the panner knob on the canvas with dynamic coloring.
    # This method renders the panner's visual elements, including the background track
    # and the active arc, which changes color based on the panner's position.
    # Inputs:
    #     canvas: The tkinter canvas to draw on.
    #     width, height (int): The dimensions of the canvas.
    #     value (float): The current value of the panner.
    #     min_val, max_val (float): The min/max values of the panner.
    #     value_label (ttk.Label): The label for displaying the current value.
    #     neutral_color, accent, secondary (str): Color values from the theme.
    # Outputs:
    #     None.
    def _draw_panner_visuals(
        self,
        canvas,
        width,
        height,
        value,
        min_val,
        max_val,
        value_label,
        neutral_color,
        accent,
        secondary,
    ):
        """
        Draws the panner knob with dynamic coloring:
        - 0 (Center): Neutral (No color spread)
        - Positive (>0): RED spreading to the right
        - Negative (<0): WHITE spreading to the left
        """
        canvas.delete("all")
        active_color = neutral_color  # Initialize with a default

        # Center circle
        cx, cy = width / 2, height / 2

        # 1. Geometry Constants
        radius = min(width, height) / 2 - 5
        start_angle = 135
        end_angle = 45
        total_angle = 270

        # 2. Draw Background Arc (The "Track")
        # tkinter arcs start from 3 o'clock (0) and go Counter-Clockwise
        # 135 degrees is bottom-left, -45 (or 315) is bottom-right.
        canvas.create_arc(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            start=270 - 45,
            extent=-270,  # Start at bottom-left, go around to bottom-right
            style=tk.ARC,
            outline=secondary,
            width=4,
        )

        # 3. Calculate Normalized Value (-1.0 to 1.0)
        # Assuming min_val is like -64 and max_val is 64
        # If value is 0, norm_val is 0.

        # Map input value to 0..1 range first
        if max_val == min_val:
            norm_val = 0
        else:
            # Map 0..1 to -1..1
            norm_val = ((value - min_val) / (max_val - min_val) * 2) - 1

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"Panner Debug: value={value}, min_val={min_val}, max_val={max_val}, norm_val={norm_val}",
                **_get_log_args(),
            )

        # 4. Determine Dynamic Color & Arc Extent
        # Center of the pot (physically) is at 90 degrees (12 o'clock)
        # 0 degrees in Tkinter is 3 o'clock. 90 is 12 o'clock.

        center_angle_tk = 90  # 12 o'clock
        max_extent = 135  # Degrees from center to either side

        if abs(norm_val) < 0.01:
            # --- DEAD CENTER (0) ---
            # Draw a simple tick mark at 12 o'clock
            active_color = neutral_color  # Neutral color
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"Panner Debug: Dead center. Active color={active_color}",
                    **_get_log_args(),
                )
            canvas.create_line(
                cx,
                cy - radius + 2,
                cx,
                cy - radius + 12,
                fill=active_color,
                width=3,
                capstyle=tk.ROUND,
            )

        else:
            # --- OFF CENTER ---
            if norm_val > 0:
                # POSITIVE -> RIGHT -> RED
                active_color = "red"  # Or a brighter red like "#FF4444"

                # Arc starts at 90 (Top) and goes Clockwise (Negative extent in Tkinter)
                # Extent is proportional to the value (0 to 1) * max_degrees
                extent = -1 * (norm_val * max_extent)

                canvas.create_arc(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    start=center_angle_tk,
                    extent=extent,
                    style=tk.ARC,
                    outline=active_color,
                    width=4,
                )

            else:
                # NEGATIVE -> LEFT -> WHITE
                active_color = "white"

                # Arc starts at 90 (Top) and goes Counter-Clockwise (Positive extent)
                # norm_val is negative, so abs(norm_val) * max_extent
                extent = abs(norm_val) * max_extent

                canvas.create_arc(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    start=center_angle_tk,
                    extent=extent,
                    style=tk.ARC,
                    outline=active_color,
                    width=4,
                )

        # Draw center oval and update label color now that active_color is set
        canvas.create_oval(
            cx - 5, cy - 6, cx + 6, cy + 6, fill=active_color, outline=active_color
        )
        value_label.config(foreground=active_color)