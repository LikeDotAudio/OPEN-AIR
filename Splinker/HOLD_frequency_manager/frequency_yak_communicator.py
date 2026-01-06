# managers/frequency_manager/frequency_yak_communicator.py
#
# This file (frequency_yak_communicator.py) handles communication with the YAK repository for frequency settings within the frequency manager.
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

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


import time
import orjson
import os
import inspect

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.logger.log_utils import _get_log_args
from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility
from .frequency_state import FrequencyState

# --- Global Scope Variables ---
LOCAL_DEBUG_ENABLE = False


class FrequencyYakCommunicator:
    """Handles communication with the YAK repository for frequency settings."""

    HZ_TO_MHZ = 1_000_000
    YAK_BASE = "OPEN-AIR/yak/Frequency"
    YAK_UPDATE_TOPIC = (
        f"{YAK_BASE}/nab/NAB_Frequency_settings/scpi_details/Execute Command/trigger"
    )

    YAK_CENTER_INPUT = f"{YAK_BASE}/set/set_center_freq_MHz/Input/hz_value/value"
    YAK_CENTER_TRIGGER = (
        f"{YAK_BASE}/set/set_center_freq_MHz/scpi_details/Execute Command/trigger"
    )

    YAK_SPAN_INPUT = f"{YAK_BASE}/set/set_span_freq_MHz/Input/hz_value/value"
    YAK_SPAN_TRIGGER = (
        f"{YAK_BASE}/set/set_span_freq_MHz/scpi_details/Execute Command/trigger"
    )

    YAK_START_INPUT = f"{YAK_BASE}/set/set_start_freq_MHz/Input/hz_value/value"
    YAK_START_TRIGGER = (
        f"{YAK_BASE}/set/set_start_freq_MHz/scpi_details/Execute Command/trigger"
    )

    YAK_STOP_INPUT = f"{YAK_BASE}/set/set_stop_freq_MHz/Input/hz_value/value"
    YAK_STOP_TRIGGER = (
        f"{YAK_BASE}/set/set_stop_freq_MHz/scpi_details/Execute Command/trigger"
    )

    YAK_NAB_OUTPUTS = {
        "start_freq/value": "Settings/fields/start_freq_MHz/value",
        "stop_freq/value": "Settings/fields/stop_freq_MHz/value",
        "center_freq/value": "Settings/fields/center_freq_MHz/value",
        "span_freq/value": "Settings/fields/span_freq_MHz/value",
    }

    def __init__(self, mqtt_controller: MqttControllerUtility, state: FrequencyState):
        self.mqtt_controller = mqtt_controller
        self.state = state
        self.base_topic = self.state.base_topic

    def publish_to_yak_and_trigger(self, value_mhz, input_topic, trigger_topic):
        current_function_name = inspect.currentframe().f_code.co_name

        try:
            value_hz = int(round(float(value_mhz) * self.HZ_TO_MHZ))

            self.mqtt_controller.publish_message(
                topic=input_topic, subtopic="", value=value_hz, retain=True
            )

            self.mqtt_controller.publish_message(
                topic=trigger_topic, subtopic="", value=True, retain=False
            )
            time.sleep(0.01)
            self.mqtt_controller.publish_message(
                topic=trigger_topic, subtopic="", value=False, retain=False
            )

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🐐✅ YAK command dispatched. Sent {value_hz} Hz to {input_topic}.",
                    **_get_log_args(),
                )

            self.update_all_from_device()

        except Exception as e:
            debug_logger(message=f"❌ Error dispatching YAK command: {e}")
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ YAK dispatch failed! The error be: {e}",
                    **_get_log_args(),
                )

    def update_all_from_device(self):
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🐐🟢 Triggering NAB_Frequency_settings to synchronize all 4 frequency values.",
                **_get_log_args(),
            )

        self.mqtt_controller.publish_message(
            topic=self.YAK_UPDATE_TOPIC, subtopic="", value=True, retain=False
        )
        time.sleep(0.01)
        self.mqtt_controller.publish_message(
            topic=self.YAK_UPDATE_TOPIC, subtopic="", value=False, retain=False
        )

        debug_logger(
            message="✅ UPDATE ALL command sent to refresh frequency values from device.",
            **_get_log_args(),
        )

    def process_yak_output(self, topic, payload):
        current_function_name = inspect.currentframe().f_code.co_name

        try:
            yak_suffix = topic.split("/Outputs/")[1]
            gui_suffix = self.YAK_NAB_OUTPUTS.get(yak_suffix)

            if not gui_suffix:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🟡 Unknown YAK output suffix: {yak_suffix}. Ignoring.",
                        **_get_log_args(),
                    )
                return

            try:
                parsed_payload = orjson.loads(payload)
                value_str = parsed_payload.get("value", payload)
            except (json.JSONDecodeError, ValueError, TypeError):
                value_str = payload

            cleaned_value = (
                str(value_str).strip().strip('"').strip("'").strip("\\").strip()
            )

            try:
                value_hz = float(cleaned_value)
                value_mhz = value_hz / self.HZ_TO_MHZ

                full_gui_topic = f"{self.base_topic}/{gui_suffix}"
                self.state._locked_state[full_gui_topic] = True

                self._publish_update(topic_suffix=gui_suffix, value=value_mhz)

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🐐✅ YAK output processed. Synced {gui_suffix} with {value_mhz} MHz.",
                        **_get_log_args(),
                    )
            except ValueError:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Could not convert YAK output '{cleaned_value}' to float for topic {topic}. Skipping update.",
                        **_get_log_args(),
                    )

        except Exception as e:
            debug_logger(message=f"❌ Error processing YAK output for {topic}: {e}")
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ NAB synchronization failed! The error be: {e}",
                    **_get_log_args(),
                )

    def _publish_update(self, topic_suffix, value):
        full_topic = f"{self.base_topic}/{topic_suffix}"
        rounded_value = round(value, 3)

        self.mqtt_controller.publish_message(
            topic=full_topic, subtopic="", value=rounded_value, retain=False
        )
