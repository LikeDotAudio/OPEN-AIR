# workers/builder/dynamic_gui_create_custom_fader.py
#
# A vertical fader widget that adapts to the system theme.
# Version 20251223.214500.ThemeFix

import tkinter as tk
from tkinter import ttk
import math
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance()     
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
from workers.styling.style import THEMES, DEFAULT_THEME
import os
from workers.mqtt.mqtt_topic_utils import get_topic

class CustomFaderFrame(tk.Frame):
    def __init__(self, master, variable, config, path, state_mirror_engine, command):
        # Extract parameters from config and provide defaults
        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.neutral_color = colors.get("neutral", "#dcdcdc")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")

        # Widget-specific config values
        self.min_val = float(config.get("value_min", -100.0))
        self.max_val = float(config.get("value_max", 0.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(config.get("reff_point", (self.min_val + self.max_val) / 2.0))
        self.border_width = int(config.get("border_width", 0))
        self.border_color = config.get("border_color", "black")
        self.show_value = config.get("show_value", True)
        self.show_units = config.get("show_units", False)
        self.label_color = config.get("label_color", "white")
        self.value_color = config.get("value_color", "white")
        self.label_text = config.get("label_active", "")
        self.outline_col = "black" # Not configurable at the moment
        self.outline_width = 1 # Not configurable at the moment
        self.ticks = config.get("ticks", None)

        super().__init__(master, bg=self.bg_color, bd=self.border_width, relief="solid", highlightbackground=self.border_color, highlightthickness=self.border_width)
        self.variable = variable
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.command = command # The function to call when value changes (e.g., on_drag_or_click)
        self.temp_entry = None # Initialize temp_entry

    def _jump_to_reff_point(self, event):
        """
        ⚡  Jumping to the Reference Point immediately!
        """
        if app_constants.global_settings['debug_enabled']:
            debug_logger(message=f"⚡ User invoked Quantum Jump! Resetting to {self.reff_point}", **_get_log_args())

        self.variable.set(self.reff_point)
        # Directly trigger MQTT update
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        
    def _open_manual_entry(self, event):
        """
        📝 User requested manual coordinate entry.
        """
        # Ensure only one entry is open at a time
        if self.temp_entry and self.temp_entry.winfo_exists():
            return

        self.temp_entry = tk.Entry(self, width=8, justify='center')
        
        # Place it exactly where the user clicked (or centered)
        self.temp_entry.place(x=event.x - 20, y=event.y - 10) 
        
        # 3. Insert current value
        current_val = self.variable.get()
        self.temp_entry.insert(0, str(current_val))
        self.temp_entry.select_range(0, tk.END) # Select all text for easy overwriting
        
        # 4. Focus so user can type immediately
        self.temp_entry.focus_set()
        
        # 5. Bind Exit Events (Enter key or Clicking away)
        self.temp_entry.bind("<Return>", self._submit_manual_entry)
        self.temp_entry.bind("<FocusOut>", self._submit_manual_entry)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

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

                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"✅ Manual entry successful: {new_value}", **_get_log_args())
            else:
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"⚠️ Value {new_value} out of bounds! Ignoring.", **_get_log_args())
                    
        except ValueError:
            # Not a number
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"❌ Invalid manual entry: '{raw_value}' is not a number.", **_get_log_args())
        
        # Cleanup
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None # Clean up the attribute

class CustomFaderCreatorMixin:
    def _create_custom_fader(self, parent_frame, label, config, path, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router):
        """Creates a custom fader widget."""
        current_function_name = "_create_custom_fader"
        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")
        handle_color = colors.get("fg", "#dcdcdc")

        # Create our custom frame type
        min_val = float(config.get("value_min", -100.0))
        max_val = float(config.get("value_max", 100.0))
        log_exponent = float(config.get("log_exponent", 1.0)) # Default to 1.0 for linear
        reff_point = float(config.get("reff_point", (min_val + max_val) / 2.0)) # Default reff_point to midpoint
        value_default = float(config.get("value_default", 75.0)) # Ensure float

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to sculpt a custom fader for '{label}'. Configured min_val={min_val}, max_val={max_val}, bg_color={bg_color}",
                **_get_log_args()
            )
        
        fader_value_var = tk.DoubleVar(value=value_default)

        def on_drag_or_click_callback(event):
            canvas = event.widget
            height = canvas.winfo_height()
            
            # Calculate normalized y position (0 at top, 1 at bottom)
            norm_y_inverted = (event.y - 10) / (height - 20)
            norm_y_inverted = max(0.0, min(1.0, norm_y_inverted)) # Clamp between 0 and 1

            # Invert normalized_y_inverted so 0 is min_val (bottom) and 1 is max_val (top)
            norm_pos = 1.0 - norm_y_inverted

            # Apply logarithmic scaling if log_exponent is not 1.0 and range is not zero
            if frame.log_exponent != 1.0 and (frame.max_val - frame.min_val) != 0:
                # Use max to prevent issues with 0 ** E when E is fractional
                log_norm_pos = max(0.0000001, norm_pos) ** frame.log_exponent
            else:
                log_norm_pos = norm_pos # Linear scaling

            # Map logarithmic normalized position to fader value
            current_value = frame.min_val + log_norm_pos * (frame.max_val - frame.min_val)
            
            # Update the Tkinter variable, triggering a redraw
            frame.variable.set(current_value)

            # Broadcast the change from the user interaction
            if state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"➡️ Custom Fader '{frame.label_text}' on_drag event triggered (y={event.y}). Value: {current_value}",
                    **_get_log_args()
                )
        frame = CustomFaderFrame(
            parent_frame,
            variable=fader_value_var,
            config=config, # Pass the entire config dictionary
            path=path,
            state_mirror_engine=state_mirror_engine,
            command=on_drag_or_click_callback # Pass the callback
        )

        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        try:
            # Layout logic handles size, but we need defaults for the canvas
            width = config.get("width", 60)
            height = config.get("height", 200)

            # Force canvas to match theme background so it blends in
            canvas = tk.Canvas(frame, width=width, height=height, bg=bg_color, highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.update_idletasks()

            # Value Label for Fader
            value_label = ttk.Label(frame, text=f"{int(fader_value_var.get())}", font=("Helvetica", 8))
            value_label.pack(side=tk.BOTTOM)

            def on_fader_value_change(*args):
                current_fader_val = fader_value_var.get()
                
                self._draw_fader(frame, canvas, canvas.winfo_width(), canvas.winfo_height(), 
                                 current_fader_val)
                
                # Determine active_color based on norm_val for the label
                norm_val = (current_fader_val - frame.min_val) / (frame.max_val - frame.min_val) if (frame.max_val - frame.min_val) != 0 else 0
                if abs(norm_val) < 0.01:
                    active_color = frame.neutral_color # Neutral color from frame
                elif norm_val > 0:
                    active_color = "red" # Hardcoded for now, could be frame.accent_color
                else:
                    active_color = "white" # Hardcoded for now, could be frame.handle_col
                value_label.config(text=f"{int(current_fader_val)}", foreground=active_color)
                
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"⚡ fluxing... Custom Fader '{frame.label_text}' updated visually to {current_fader_val} from MQTT.",
                        **_get_log_args()
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
            canvas.bind("<Configure>", lambda e: on_fader_value_change()) # Redraw on resize

            # Register the StringVar with the StateMirrorEngine for MQTT updates
            if path:
                widget_id = path
                state_mirror_engine.register_widget(widget_id, fader_value_var, base_mqtt_topic_from_path, config)
                
                # Subscribe to the topic for incoming messages
                topic = get_topic("OPEN-AIR", base_mqtt_topic_from_path, widget_id)
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)

                if app_constants.global_settings['debug_enabled']:
                                debug_logger(
                                    message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (DoubleVar: {fader_value_var.get()}).",
                                    **_get_log_args()
                                )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ SUCCESS! The custom fader for '{label}' has been meticulously carved!",
                    **_get_log_args()
                )
            return frame
        except Exception as e:
            debug_logger(message=f"❌ The custom fader for '{label}' melted! Error: {e}")
            return None


    def _draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [x1 + radius, y1,
                x1 + radius, y1,
                x2 - radius, y1,
                x2 - radius, y1,
                x2, y1,
                x2, y1 + radius,
                x2, y1 + radius,
                x2, y2 - radius,
                x2, y2 - radius,
                x2, y2,
                x2 - radius, y2,
                x2 - radius, y2,
                x1 + radius, y2,
                x1 + radius, y2,
                x1, y2,
                x1, y2 - radius,
                x1, y2 - radius,
                x1, y1 + radius,
                x1, y1 + radius,
                x1, y1]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def _draw_fader(self, frame_instance, canvas, width, height, value):
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🎨 Drawing fader: value={value}, min_val={frame_instance.min_val}, max_val={frame_instance.max_val}, height={height}",
                **_get_log_args()
            )
        canvas.delete("all")        
        # Center Line
        cx = width / 2
        
        # Track (Groove)
        canvas.create_line(cx, 10, cx, height-10, fill=frame_instance.track_col, width=4, capstyle=tk.ROUND)
        
        # Calculate handle position based on logarithmic scale
        # Normalize the current value to a 0-1 range (0 for min_val, 1 for max_val)
        norm_value = (value - frame_instance.min_val) / (frame_instance.max_val - frame_instance.min_val) if (frame_instance.max_val - frame_instance.min_val) != 0 else 0
        norm_value = max(0.0, min(1.0, norm_value)) # Clamp to ensure it's within 0-1

        # Apply inverse logarithmic scaling if log_exponent is not 1.0 and range is not zero
        if frame_instance.log_exponent != 1.0 and (frame_instance.max_val - frame_instance.min_val) != 0:
            # Use max to prevent issues with 0 ** (1/E) when norm_value is 0 or very close
            display_norm_pos = max(0.0000001, norm_value) ** (1.0 / frame_instance.log_exponent)
        else:
            display_norm_pos = norm_value # Linear display position

        # Invert display_norm_pos because y=0 is top (max_val), y=1 is bottom (min_val)
        handle_y_norm = 1.0 - display_norm_pos

        # Scale to canvas coordinates
        handle_y = (height - 20) * handle_y_norm + 10
        
        # Draw Tick Marks
        tick_color = "light grey"  # User requested light grey
        tick_length_half = width * 0.1 # Small tick marks, 10% of width on each side

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
            else: # Handle case where max_val <= min_val, though unlikely for fader range
                start_tick = math.floor(frame_instance.min_val / 5) * 5
                end_tick = math.ceil(frame_instance.max_val / 5) * 5
                step = -5 # Iterate downwards
            
            tick_values = range(int(start_tick), int(end_tick) + 1, int(step))

        for i, tick_value in enumerate(tick_values):
            # Calculate linear normalized position for the tick value
            linear_tick_norm = (tick_value - frame_instance.min_val) / (frame_instance.max_val - frame_instance.min_val) if (frame_instance.max_val - frame_instance.min_val) != 0 else 0
            linear_tick_norm = max(0.0, min(1.0, linear_tick_norm)) # Clamp for safety

            # Apply inverse logarithmic scaling for display position
            if frame_instance.log_exponent != 1.0 and (frame_instance.max_val - frame_instance.min_val) != 0:
                # Use max to prevent issues with 0 ** (1/E) when linear_tick_norm is 0 or very close
                display_tick_norm = max(0.0000001, linear_tick_norm) ** (1.0 / frame_instance.log_exponent)
            else:
                display_tick_norm = linear_tick_norm # Linear display position

            # Invert display_tick_norm because y=0 is top (max_val), y=1 is bottom (min_val)
            tick_y_pos = (height - 20) * (1 - display_tick_norm) + 10
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"📊 Fader Tick: value={tick_value}, linear_norm={linear_tick_norm:.3f}, display_norm={display_tick_norm:.3f}, y_pos={tick_y_pos:.2f}",
                    **_get_log_args()
                )
            # Draw a short line for the tick mark
            canvas.create_line(cx - tick_length_half, tick_y_pos, cx + tick_length_half, tick_y_pos, fill=tick_color, width=1)
            
            # Draw tick value label for every other tick
            if i % 2 == 0:
                canvas.create_text(cx + 15, tick_y_pos, text=str(int(tick_value)), fill=tick_color, anchor="w")
        
        # Determine active_color based on norm_value (using the actual norm_value, not display_norm_pos)
        if abs(norm_value) < 0.01:
            active_color = frame_instance.neutral_color # Neutral color
        elif norm_value > 0:
            active_color = "red"
        else:
            active_color = "white"

        # Handle (Fader Cap)
        cap_width = 40 # Set fixed cap width to 40 pixels
        cap_height = 50
        self._draw_rounded_rectangle(
            canvas,
            cx - cap_width/2, handle_y - cap_height/2,
            cx + cap_width/2, handle_y + cap_height/2,
            radius=10,
            fill=frame_instance.handle_col, outline=frame_instance.track_col
        )
        # Center line
        center_line_length = cap_width * 0.9
        canvas.create_line(cx - center_line_length/2, handle_y, cx + center_line_length/2, handle_y, fill=frame_instance.track_col, width=2)
        
        # 60% lines at 25% and 75% of height
        side_line_length = cap_width * 0.6
        y_offset = cap_height * 0.25
        canvas.create_line(cx - side_line_length/2, handle_y - y_offset, cx + side_line_length/2, handle_y - y_offset, fill=frame_instance.track_col, width=1)
        canvas.create_line(cx - side_line_length/2, handle_y + y_offset, cx + side_line_length/2, handle_y + y_offset, fill=frame_instance.track_col, width=1)