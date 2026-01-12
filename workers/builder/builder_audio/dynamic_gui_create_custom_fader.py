# builder_audio/dynamic_gui_create_custom_fader.py
#
# A vertical fader widget that adapts to the system theme.
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
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace


class CustomFaderFrame(tk.Frame):
    # Initializes the CustomFaderFrame widget.
    # This constructor sets up the fader with its visual properties and behavior based on the
    # provided configuration. It defines colors, value ranges, and other display attributes.
    # Inputs:
    #     master: The parent tkinter widget.
    #     variable (tk.DoubleVar): The tkinter variable to bind to the fader's value.
    #     config (dict): A dictionary containing configuration settings for the fader.
    #     path (str): The widget's unique identifier path for state management.
    #     state_mirror_engine: The engine for synchronizing state with the MQTT broker.
    #     command (function): The callback function to execute when the fader's value changes.
    # Outputs:
    #     None.
    def __init__(self, master, variable, config, path, state_mirror_engine, command):
        # Extract parameters from config and provide defaults
        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        fader_style = colors.get("fader_style", {})
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.neutral_color = colors.get("neutral", "#dcdcdc")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")

        # Widget-specific config values
        self.min_val = float(config.get("value_min", -100.0))
        self.max_val = float(config.get("value_max", 0.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(
            config.get("reff_point", (self.min_val + self.max_val) / 2.0)
        )
        self.border_width = int(config.get("border_width", 0))
        self.border_color = config.get("border_color", "black")
        self.show_value = config.get("show_value", True)
        self.show_units = config.get("show_units", False)
        self.label_color = config.get("label_color", "white")
        self.value_color = config.get("value_color", "white")
        self.label_text = config.get("label_active", "")
        self.outline_col = "black"  # Not configurable at the moment
        self.outline_width = 1  # Not configurable at the moment
        self.ticks = config.get("ticks", None)

        # Custom styling
        self.tick_size = config.get("tick_size", fader_style.get("tick_size", 0.1))
        tick_font_family = config.get("tick_font_family", fader_style.get("tick_font_family", "Helvetica"))
        tick_font_size = config.get("tick_font_size", fader_style.get("tick_font_size", 10))
        self.tick_font = (tick_font_family, tick_font_size)
        self.tick_color = config.get("tick_color", fader_style.get("tick_color", "light grey"))
        self.value_follow = config.get("value_follow", fader_style.get("value_follow", True))
        self.value_highlight_color = config.get("value_highlight_color", fader_style.get("value_highlight_color", "#f4902c"))

        super().__init__(
            master,
            bg=self.bg_color,
            bd=self.border_width,
            relief="solid",
            highlightbackground=self.border_color,
            highlightthickness=self.border_width,
        )
        self.variable = variable
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.command = (
            command  # The function to call when value changes (e.g., on_drag_or_click)
        )
        self.temp_entry = None  # Initialize temp_entry

    # Sets the fader's value to its predefined reference point.
    # This method is typically triggered by a user action, such as a specific mouse click,
    # and provides a quick way to reset the fader to a default or common value.
    # Inputs:
    #     event: The tkinter event object that triggered the call.
    # Outputs:
    #     None.
    def _jump_to_reff_point(self, event):
        """
        ⚡  Jumping to the Reference Point immediately!
        """
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"⚡ User invoked Quantum Jump! Resetting to {self.reff_point}",
                **_get_log_args(),
            )

        self.variable.set(self.reff_point)
        # Directly trigger MQTT update
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    # Opens a temporary entry widget for manual value input.
    # This allows the user to type in a precise value for the fader, bypassing mouse interaction.
    # The entry widget is placed at the cursor's position for convenience.
    # Inputs:
    #     event: The tkinter event object, used to position the entry widget.
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

    # Submits the value entered in the manual entry widget.
    # This method validates the entered value, ensures it is within the fader's bounds,
    # and if valid, updates the fader's state and triggers a state broadcast.
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
    # This is a cleanup method to remove the entry widget after its use.
    # Inputs:
    #     event: The tkinter event object.
    # Outputs:
    #     None.
    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None  # Clean up the attribute


class CustomFaderCreatorMixin:
    # Creates a custom fader widget and its associated components.
    # This method handles the entire creation process for a fader, including setting up
    # its tkinter variable, defining its drag-and-click behavior, and registering it with
    # the state management engine.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration dictionary for the fader.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     CustomFaderFrame: The created fader frame widget, or None on failure.
    def _create_custom_fader(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a custom fader widget."""
        current_function_name = "_create_custom_fader"

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")
        handle_color = colors.get("fg", "#dcdcdc")

        # Create our custom frame type
        min_val = float(config.get("value_min", -100.0))
        max_val = float(config.get("value_max", 0.0))
        log_exponent = float(
            config.get("log_exponent", 1.0)
        )  # Default to 1.0 for linear
        reff_point = float(
            config.get("reff_point", (min_val + max_val) / 2.0)
        )  # Default reff_point to midpoint
        value_default = float(config.get("value_default", 75.0))  # Ensure float

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to sculpt a custom fader for '{label}'. Configured min_val={min_val}, max_val={max_val}, bg_color={bg_color}",
                **_get_log_args(),
            )

        fader_value_var = tk.DoubleVar(value=value_default)

        def on_drag_or_click_callback(event):
            canvas = event.widget
            height = canvas.winfo_height()

            # Calculate normalized y position (0 at top, 1 at bottom)
            norm_y_inverted = (event.y - 10) / (height - 20)
            norm_y_inverted = max(
                0.0, min(1.0, norm_y_inverted)
            )  # Clamp between 0 and 1

            # Invert normalized_y_inverted so 0 is min_val (bottom) and 1 is max_val (top)
            norm_pos = 1.0 - norm_y_inverted

            # Apply logarithmic scaling if log_exponent is not 1.0 and range is not zero
            if frame.log_exponent != 1.0 and (frame.max_val - frame.min_val) != 0:
                # Use max to prevent issues with 0 ** E when E is fractional
                log_norm_pos = max(0.0000001, norm_pos) ** frame.log_exponent
            else:
                log_norm_pos = norm_pos  # Linear scaling

            # Map logarithmic normalized position to fader value
            current_value = frame.min_val + log_norm_pos * (
                frame.max_val - frame.min_val
            )

            # Update the Tkinter variable, triggering a redraw
            frame.variable.set(current_value)

            # Broadcast the change from the user interaction
            if state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"➡️ Custom Fader '{frame.label_text}' on_drag event triggered (y={event.y}). Value: {current_value}",
                    **_get_log_args(),
                )

        frame = CustomFaderFrame(
            parent_widget,  # Use parent_widget here
            variable=fader_value_var,
            config=config,  # Pass the entire config dictionary
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=on_drag_or_click_callback,  # Pass the callback
        )

        layout_config = config.get("layout", {})
        font_size = layout_config.get("font", 10)
        custom_font = ("Helvetica", font_size)
        custom_colour = layout_config.get("colour", None)

        if label:
            lbl = tk.Label(frame, text=label, font=custom_font, background=bg_color, foreground=fg_color)
            if custom_colour:
                lbl.configure(foreground=custom_colour)
            lbl.pack(side=tk.TOP, pady=(0, 5))

        try:
            # Layout logic handles size, but we need defaults for the canvas
            width = layout_config.get("width", 60)
            height = layout_config.get("height", 200)

            # Force canvas to match theme background so it blends in
            canvas = tk.Canvas(
                frame, width=width, height=height, bg=bg_color, highlightthickness=0
            )
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.update_idletasks()

            # Value Label for Fader
            value_label = tk.Label(
                frame, text=f"{int(fader_value_var.get())}", font=("Helvetica", 8), background=bg_color, foreground=fg_color
            )
            value_label.pack(side=tk.BOTTOM)

            def on_fader_value_change(*args):
                current_fader_val = fader_value_var.get()

                # Use winfo or fall back to config dimensions if not yet mapped
                current_w = canvas.winfo_width()
                current_h = canvas.winfo_height()
                if current_w <= 1: current_w = width
                if current_h <= 1: current_h = height

                self._draw_fader(
                    frame,
                    canvas,
                    current_w,
                    current_h,
                    current_fader_val,
                )

                # Determine active_color based on norm_val for the label
                norm_val = (
                    (current_fader_val - frame.min_val)
                    / (frame.max_val - frame.min_val)
                    if (frame.max_val - frame.min_val) != 0
                    else 0
                )
                if abs(norm_val) < 0.01:
                    active_color = frame.neutral_color  # Neutral color from frame
                else:
                    active_color = frame.value_highlight_color

                value_label.config(
                    text=f"{int(current_fader_val)}", foreground=active_color
                )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚡ fluxing... Custom Fader '{frame.label_text}' updated visually to {current_fader_val} from MQTT.",
                        **_get_log_args(),
                    )

            fader_value_var.trace_add("write", on_fader_value_change)

            # Initial draw based on default value
            on_fader_value_change()

            # Interaction
            canvas.bind("<B1-Motion>", frame.command)
            canvas.bind("<Button-1>", frame.command)

            # --- Bind Special Keys for Quantum Jump and Precise Entry ---
            canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)

            # Handle Resize
            canvas.bind(
                "<Configure>", lambda e: on_fader_value_change()
            )  # Redraw on resize

            # Register the StringVar with the StateMirrorEngine for MQTT updates
            if path:
                widget_id = path
                self.state_mirror_engine.register_widget(
                    widget_id, fader_value_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to the topic for incoming messages
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id)
                self.subscriber_router.subscribe_to_topic(
                    topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (DoubleVar: {fader_value_var.get()}).",
                        **_get_log_args(),
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The custom fader for '{label}' has been meticulously carved!",
                    **_get_log_args(),
                )
            return frame
        except Exception as e:
            debug_logger(
                message=f"❌ The custom fader for '{label}' melted! Error: {e}"
            )
            return None

    # Draws a rectangle with rounded corners on a tkinter canvas.
    # This is a utility function used for creating custom-shaped widgets.
    # Inputs:
    #     canvas: The tkinter canvas to draw on.
    #     x1, y1, x2, y2 (int): The coordinates of the bounding box.
    #     radius (int): The corner radius.
    #     **kwargs: Additional keyword arguments for the canvas polygon item.
    # Outputs:
    #     int: The ID of the created canvas item.
    def _draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius,
            y1,
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    # Draws the custom fader widget on the canvas.
    # This method is responsible for all the visual elements of the fader, including the track,
    # handle (cap), and tick marks. It calculates positions based on a logarithmic scale if specified.
    # Inputs:
    #     frame_instance (CustomFaderFrame): The fader frame instance containing config.
    #     canvas: The tkinter canvas to draw on.
    #     width, height (int): The dimensions of the canvas.
    #     value (float): The current value of the fader.
    # Outputs:
    #     None.
    def _draw_fader(self, frame_instance, canvas, width, height, value):
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🎨 Drawing fader: value={value}, min_val={frame_instance.min_val}, max_val={frame_instance.max_val}, height={height}",
                **_get_log_args(),
            )
        canvas.delete("all")
        # Center Line
        cx = width / 2

        # Track (Groove)
        canvas.create_line(
            cx,
            10,
            cx,
            height - 10,
            fill=frame_instance.track_col,
            width=4,
            capstyle=tk.ROUND,
        )

        # Calculate handle position based on logarithmic scale
        # Normalize the current value to a 0-1 range (0 for min_val, 1 for max_val)
        norm_value = (
            (value - frame_instance.min_val)
            / (frame_instance.max_val - frame_instance.min_val)
            if (frame_instance.max_val - frame_instance.min_val) != 0
            else 0
        )
        norm_value = max(0.0, min(1.0, norm_value))  # Clamp to ensure it's within 0-1

        # Apply inverse logarithmic scaling if log_exponent is not 1.0 and range is not zero
        if (
            frame_instance.log_exponent != 1.0
            and (frame_instance.max_val - frame_instance.min_val) != 0
        ):
            # Use max to prevent issues with 0 ** (1/E) when norm_value is 0 or very close
            display_norm_pos = max(0.0000001, norm_value) ** (
                1.0 / frame_instance.log_exponent
            )
        else:
            display_norm_pos = norm_value  # Linear display position

        # Invert display_norm_pos because y=0 is top (max_val), y=1 is bottom (min_val)
        handle_y_norm = 1.0 - display_norm_pos

        # Scale to canvas coordinates
        handle_y = (height - 20) * handle_y_norm + 10

        # Draw Tick Marks
        tick_length_half = width * frame_instance.tick_size

        tick_values = []
        if frame_instance.ticks is not None:
            tick_values = frame_instance.ticks
        else:
            # Determine step for displaying ticks. User requested intervals of 5.
            # Ensure that min_val, max_val, and interval are handled correctly for iteration direction.
            if frame_instance.min_val < frame_instance.max_val:
                start_tick = math.ceil(frame_instance.min_val / 5) * 5
                end_tick = math.floor(frame_instance.max_val / 5) * 5
                step = 5
            else:  # Handle case where max_val <= min_val, though unlikely for fader range
                start_tick = math.floor(frame_instance.min_val / 5) * 5
                end_tick = math.ceil(frame_instance.max_val / 5) * 5
                step = -5  # Iterate downwards

            tick_values = range(int(start_tick), int(end_tick) + 1, int(step))

        for i, tick_value in enumerate(tick_values):
            # Calculate linear normalized position for the tick value
            linear_tick_norm = (
                (tick_value - frame_instance.min_val)
                / (frame_instance.max_val - frame_instance.min_val)
                if (frame_instance.max_val - frame_instance.min_val) != 0
                else 0
            )
            linear_tick_norm = max(0.0, min(1.0, linear_tick_norm))  # Clamp for safety

            # Apply inverse logarithmic scaling for display position
            if (
                frame_instance.log_exponent != 1.0
                and (frame_instance.max_val - frame_instance.min_val) != 0
            ):
                # Use max to prevent issues with 0 ** (1/E) when linear_tick_norm is 0 or very close
                display_tick_norm = max(0.0000001, linear_tick_norm) ** (
                    1.0 / frame_instance.log_exponent
                )
            else:
                display_tick_norm = linear_tick_norm  # Linear display position

            # Invert display_tick_norm because y=0 is top (max_val), y=1 is bottom (min_val)
            tick_y_pos = (height - 20) * (1 - display_tick_norm) + 10

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"📊 Fader Tick: value={tick_value}, linear_norm={linear_tick_norm:.3f}, display_norm={display_tick_norm:.3f}, y_pos={tick_y_pos:.2f}",
                    **_get_log_args(),
                )
            # Draw a short line for the tick mark
            canvas.create_line(
                cx - tick_length_half,
                tick_y_pos,
                cx + tick_length_half,
                tick_y_pos,
                fill=frame_instance.tick_color,
                width=1,
            )

            # Draw tick value label for every other tick
            if i % 2 == 0:
                canvas.create_text(
                    cx + 15,
                    tick_y_pos,
                    text=str(int(tick_value)),
                    fill=frame_instance.tick_color,
                    font=frame_instance.tick_font,
                    anchor="w",
                )

        # Determine active_color based on norm_value (using the actual norm_value, not display_norm_pos)
        if abs(norm_value) < 0.01:
            active_color = frame_instance.neutral_color  # Neutral color
        else:
            active_color = frame_instance.value_highlight_color

        # Handle (Fader Cap)
        cap_width = 40  # Set fixed cap width to 40 pixels
        cap_height = 50
        self._draw_rounded_rectangle(
            canvas,
            cx - cap_width / 2,
            handle_y - cap_height / 2,
            cx + cap_width / 2,
            handle_y + cap_height / 2,
            radius=10,
            fill=frame_instance.handle_col,
            outline=frame_instance.track_col,
        )

        if frame_instance.value_follow:
            canvas.create_text(
                cx,
                handle_y - cap_height / 2 - 5,
                text=f"{value:.2f}",
                fill=frame_instance.value_color,
                anchor="s"
            )

        # Center line
        center_line_length = cap_width * 0.9
        canvas.create_line(
            cx - center_line_length / 2,
            handle_y,
            cx + center_line_length / 2,
            handle_y,
            fill=frame_instance.track_col,
            width=2,
        )

        # 60% lines at 25% and 75% of height
        side_line_length = cap_width * 0.6
        y_offset = cap_height * 0.25
        canvas.create_line(
            cx - side_line_length / 2,
            handle_y - y_offset,
            cx + side_line_length / 2,
            handle_y - y_offset,
            fill=frame_instance.track_col,
            width=1,
        )
        canvas.create_line(
            cx - side_line_length / 2,
            handle_y + y_offset,
            cx + side_line_length / 2,
            handle_y + y_offset,
            fill=frame_instance.track_col,
            width=1,
        )