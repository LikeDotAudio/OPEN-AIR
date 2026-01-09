# builder_data_graphing/Meter_to_display_units.py
#
# A Tkinter widget that displays a numerical value with progress bars.
# Now publishes standard 'val' envelopes to the widget's root topic.
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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from collections import deque
import time
import math
from typing import Dict, Any, List
import inspect
import orjson  # Ensure orjson is imported

from workers.logger.logger import debug_logger
from managers.configini.config_reader import Config
from workers.logger.log_utils import _get_log_args
from workers.mqtt.mqtt_publisher_service import publish_payload
from workers.mqtt.mqtt_topic_utils import get_topic

app_constants = Config.get_instance()


class HorizontalMeterWithText(ttk.Frame):
    """
    A Tkinter widget that displays a numerical value with progress bars.
    Now publishes standard 'val' envelopes to the widget's root topic.
    """

    # Initializes the HorizontalMeterWithText widget.
    # This constructor sets up a meter with a title, a main value display,
    # integer and decimal progress bars, and labels. It also integrates with
    # the state management engine for MQTT synchronization.
    # Inputs:
    #     parent: The parent tkinter widget.
    #     config (Dict[str, Any]): Configuration settings for the meter.
    #     base_mqtt_topic_from_path (str): The base MQTT topic for the widget.
    #     widget_id (str): The unique identifier for the widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     None.
    def __init__(
        self,
        parent,
        config: Dict[str, Any],
        base_mqtt_topic_from_path: str,
        widget_id: str,
        **kwargs,
    ):
        self.subscriber_router = kwargs.pop("subscriber_router", None)
        self.state_mirror_engine = kwargs.pop("state_mirror_engine", None)
        super().__init__(parent, **kwargs)
        self.config = config
        self.base_mqtt_topic_from_path = base_mqtt_topic_from_path
        self.widget_id = widget_id

        # 🧪 Temporal Alignment: Fetch the GUID
        self.GUID = "UNKNOWN_GUID"
        if self.state_mirror_engine and hasattr(self.state_mirror_engine, "GUID"):
            self.GUID = self.state_mirror_engine.GUID

        self.title_text = config.get("title", "Meter")
        self.max_integer_value = config.get("max_integer_value", 100)

        # --- Introduce tk.DoubleVar for state management ---
        self.meter_value_var = tk.DoubleVar(value=config.get("value_default", 0.0))

        # --- UI Construction ---
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)

        self.label_title = ttk.Label(
            self.header_frame, text=self.title_text, anchor="w"
        )
        self.label_title.pack(side=tk.LEFT, padx=2)

        self.label_value = ttk.Label(self.header_frame, text="Value: --", anchor="e")
        self.label_value.pack(side=tk.RIGHT, padx=2)

        self.int_frame = ttk.Frame(self)
        self.int_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))

        self.bar_graph_value1 = ttk.Progressbar(
            self.int_frame, orient="horizontal", length=200, mode="determinate"
        )
        self.bar_graph_value1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.bar_graph_value1["maximum"] = self.max_integer_value

        self.label1 = ttk.Label(self.int_frame, text="Int: --", width=8, anchor="w")
        self.label1.pack(side=tk.RIGHT, padx=2)

        self.dec_frame = ttk.Frame(self)
        self.dec_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        self.bar_graph_value_dec = ttk.Progressbar(
            self.dec_frame, orient="horizontal", length=200, mode="determinate"
        )
        self.bar_graph_value_dec.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.bar_graph_value_dec["maximum"] = 100

        self.label_dec = ttk.Label(self.dec_frame, text="Dec: --", width=8, anchor="w")
        self.label_dec.pack(side=tk.RIGHT, padx=2)

        # Bind update logic to the meter_value_var's trace
        self.meter_value_var.trace_add("write", self._on_meter_value_var_change)
        # Initial display update
        self._on_meter_value_var_change()

        # 📡 Register with StateMirrorEngine (handles subscription automatically)
        if self.state_mirror_engine:
            self.state_mirror_engine.register_widget(
                self.widget_id,
                self.meter_value_var,
                self.base_mqtt_topic_from_path,
                self.config,
            )
            self.state_mirror_engine.initialize_widget_state(self.widget_id)

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🧪 Meter '{self.widget_id}' initialized. GUID: {self.GUID}",
                **_get_log_args(),
            )

    # Callback for when the meter's numerical value changes.
    # This method updates the display of the meter, including the main value label,
    # integer and decimal progress bars, and color-codes the value based on its sign.
    # It also publishes the new value to the MQTT broker.
    # Inputs:
    #     *args: Arguments passed by the tkinter variable trace.
    # Outputs:
    #     None.
    def _on_meter_value_var_change(self, *args):
        """Callback for when meter_value_var changes (from internal or MQTT)."""
        new_value = self.meter_value_var.get()
        # Update UI
        self.label_value.config(text=f"Value: {new_value:.3f}")
        truncated_value = math.trunc(new_value)
        decimal_part = abs(new_value - truncated_value) * 100
        self.bar_graph_value1["value"] = min(
            abs(truncated_value), self.max_integer_value
        )
        self.label1.config(text=f"Int: {truncated_value}")
        self.bar_graph_value_dec["value"] = decimal_part
        self.label_dec.config(text=f"Dec: {int(decimal_part)}")

        if new_value < 0:
            self.label_value.config(foreground="red")
        else:
            self.label_value.config(foreground="black")

        # 🚀 Publish Standardized State (only if initiated by user interaction, not self-echo)
        # The _silent_update mechanism in StateMirrorEngine handles preventing echoes
        try:
            if self.state_mirror_engine and not self.state_mirror_engine._silent_update:
                base_topic = (
                    self.state_mirror_engine.base_topic
                    if self.state_mirror_engine
                    else "OPEN-AIR"
                )
                topic = get_topic(
                    base_topic, self.base_mqtt_topic_from_path, self.widget_id
                )

                payload = {
                    "val": new_value,
                    "ts": time.time(),
                    "GUID": self.GUID,
                    "src": "HorizontalMeter",
                }
                publish_payload(topic, orjson.dumps(payload), retain=True)

        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    f"❌ Error publishing value for {self.widget_id}: {e}",
                    **_get_log_args(),
                )


class VerticalMeter(ttk.Frame):
    """
    A Tkinter widget to simulate a 4-channel vertical meter display.
    Now publishes standard 'val' envelopes to the widget's root topic.
    """

    # Initializes the VerticalMeter widget.
    # This constructor sets up a multi-channel vertical meter display, creating labels
    # for each channel. It binds a tkinter StringVar to hold the JSON string of values,
    # enabling updates and synchronization via MQTT.
    # Inputs:
    #     parent: The parent tkinter widget.
    #     config (Dict[str, Any]): Configuration settings for the meter.
    #     base_mqtt_topic_from_path (str): The base MQTT topic for the widget.
    #     widget_id (str): The unique identifier for the widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     None.
    def __init__(
        self,
        parent,
        config: Dict[str, Any],
        base_mqtt_topic_from_path: str,
        widget_id: str,
        **kwargs,
    ):
        self.subscriber_router = kwargs.pop("subscriber_router", None)
        self.state_mirror_engine = kwargs.pop("state_mirror_engine", None)
        super().__init__(parent, **kwargs)
        self.config = config
        self.base_mqtt_topic_from_path = base_mqtt_topic_from_path
        self.widget_id = widget_id

        # 🧪 Temporal Alignment
        self.GUID = "UNKNOWN_GUID"
        if self.state_mirror_engine and hasattr(self.state_mirror_engine, "GUID"):
            self.GUID = self.state_mirror_engine.GUID

        self.channel_labels: List[ttk.Label] = []
        num_channels = config.get("num_channels", 4)

        # Introduce a tk.StringVar to hold the JSON string of values
        self.meter_values_var = tk.StringVar(
            value=orjson.dumps(
                [config.get("value_default", 0.0)] * num_channels
            ).decode()
        )

        for i in range(num_channels):
            label = ttk.Label(self, text=f"Ch {i+1}: --", anchor="w")
            label.pack(side=tk.TOP, fill=tk.X, pady=1)
            self.channel_labels.append(label)

        # Bind update logic to the meter_values_var's trace
        self.meter_values_var.trace_add("write", self._on_meter_values_var_change)
        # Initial display update
        self._on_meter_values_var_change()

        # 📡 Register with StateMirrorEngine (handles subscription automatically)
        if self.state_mirror_engine:
            self.state_mirror_engine.register_widget(
                self.widget_id,
                self.meter_values_var,
                self.base_mqtt_topic_from_path,
                self.config,
            )
            self.state_mirror_engine.initialize_widget_state(self.widget_id)

    # Callback for when the meter's values (JSON string) change.
    # This method parses the incoming JSON string, extracts numerical values for each channel,
    # updates the corresponding labels in the GUI, and publishes the new values to MQTT.
    # Inputs:
    #     *args: Arguments passed by the tkinter variable trace.
    # Outputs:
    #     None.
    def _on_meter_values_var_change(self, *args):
        """Callback for when meter_values_var changes (from internal or MQTT)."""
        new_values_str = self.meter_values_var.get()
        try:
            # This logic is designed to be very tolerant of poorly-formatted list-like strings.
            import re

            number_strings = re.findall(r"-?\d*\.?\d+", new_values_str)
            new_values = []
            for n_str in number_strings:
                try:
                    new_values.append(float(n_str))
                except ValueError:
                    debug_logger(
                        f"⚠️ Could not convert '{n_str}' to float in VerticalMeter.",
                        **_get_log_args(),
                    )
                    continue

            # Update UI
            for i, value in enumerate(new_values):
                if i < len(self.channel_labels):
                    self.channel_labels[i].config(text=f"Ch {i+1}: {float(value):.2f}")

            # 🚀 Publish Standardized State (only if initiated by user interaction, not self-echo)
            try:
                if (
                    self.state_mirror_engine
                    and not self.state_mirror_engine._silent_update
                ):
                    base_topic = (
                        self.state_mirror_engine.base_topic
                        if self.state_mirror_engine
                        else "OPEN-AIR"
                    )
                    topic = get_topic(
                        base_topic, self.base_mqtt_topic_from_path, self.widget_id
                    )

                    payload = {
                        "val": new_values,  # The list is now the main 'val'
                        "ts": time.time(),
                        "GUID": self.GUID,
                        "src": "VerticalMeter",
                    }
                    publish_payload(topic, orjson.dumps(payload), retain=True)

            except Exception as e:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        f"❌ Error publishing values for {self.widget_id}: {e}",
                        **_get_log_args(),
                    )

        except (ValueError, TypeError) as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    f"❌ Error processing meter_values_var: {e}", **_get_log_args()
                )


if __name__ == "__main__":
    # Example usage remains the same
    pass