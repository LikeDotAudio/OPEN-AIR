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


import orjson
import os
import inspect

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.logger.log_utils import _get_log_args
from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility
from .frequency_state import FrequencyState
from .frequency_yak_communicator import FrequencyYakCommunicator

# --- Global Scope Variables ---
LOCAL_DEBUG_ENABLE = False


class FrequencyCallbacks:
    """Handles MQTT message callbacks and logic for frequency settings."""

    def __init__(
        self,
        mqtt_controller: MqttControllerUtility,
        state: FrequencyState,
        yak_communicator: FrequencyYakCommunicator,
    ):
        self.mqtt_controller = mqtt_controller
        self.state = state
        self.yak_communicator = yak_communicator
        self.base_topic = self.state.base_topic

    def subscribe_to_topics(self):
        current_function_name = inspect.currentframe().f_code.co_name

        topic_list = [
            f"{self.base_topic}/Settings/fields/center_freq_MHz/value",
            f"{self.base_topic}/Settings/fields/span_freq_MHz/value",
            f"{self.base_topic}/Settings/fields/start_freq_MHz/value",
            f"{self.base_topic}/Settings/fields/stop_freq_MHz/value",
        ]

        for topic in topic_list:
            self.mqtt_controller.add_subscriber(
                topic_filter=topic, callback_func=self.on_message
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(message=f"🔍 Subscribed to '{topic}'.", **_get_log_args())

        for yak_suffix in self.yak_communicator.YAK_NAB_OUTPUTS.keys():
            yak_topic = f"{self.yak_communicator.YAK_BASE}/nab/NAB_Frequency_settings/Outputs/{yak_suffix}"
            self.mqtt_controller.add_subscriber(
                topic_filter=yak_topic, callback_func=self.on_message
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🔍 Subscribed to YAK output '{yak_topic}'.",
                    **_get_log_args(),
                )

    def on_message(self, topic, payload):
        current_function_name = inspect.currentframe().f_code.co_name

        if topic.startswith(
            f"{self.yak_communicator.YAK_BASE}/nab/NAB_Frequency_settings/Outputs"
        ):
            self.yak_communicator.process_yak_output(topic, payload)
            return

        if self.state._locked_state.get(topic, False):
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🟡 Message on locked topic '{topic}' received. Ignoring to prevent loop.",
                    **_get_log_args(),
                )
            self.state._locked_state[topic] = False
            return

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🔵 Received message on topic '{topic}' with payload '{payload}'. Executing synchronization logic.",
                **_get_log_args(),
            )

        try:
            try:
                parsed_payload = orjson.loads(payload)
                value_str = parsed_payload.get("value", payload)
            except (json.JSONDecodeError, TypeError):
                value_str = payload

            value = str(value_str).strip().strip('"').strip("'")

            if "center_freq_MHz/value" in topic:
                new_val = float(value)
                if (
                    self.state.center_freq is None
                    or abs(self.state.center_freq - new_val) > 0.001
                ):
                    self.state.center_freq = new_val
                    self._update_start_stop_from_center_span()
                    self.yak_communicator.publish_to_yak_and_trigger(
                        new_val,
                        self.yak_communicator.YAK_CENTER_INPUT,
                        self.yak_communicator.YAK_CENTER_TRIGGER,
                    )
            elif "span_freq_MHz/value" in topic:
                new_val = float(value)
                if (
                    self.state.span_freq is None
                    or abs(self.state.span_freq - new_val) > 0.001
                ):
                    self.state.span_freq = new_val
                    self._update_start_stop_from_center_span()
                    self.yak_communicator.publish_to_yak_and_trigger(
                        new_val,
                        self.yak_communicator.YAK_SPAN_INPUT,
                        self.yak_communicator.YAK_SPAN_TRIGGER,
                    )
            elif "start_freq_MHz/value" in topic:
                new_val = float(value)
                if (
                    self.state.start_freq is None
                    or abs(self.state.start_freq - new_val) > 0.001
                ):
                    self.state.start_freq = new_val
                    self._update_center_and_span_from_start_stop()
                    self.yak_communicator.publish_to_yak_and_trigger(
                        new_val,
                        self.yak_communicator.YAK_START_INPUT,
                        self.yak_communicator.YAK_START_TRIGGER,
                    )
            elif "stop_freq_MHz/value" in topic:
                new_val = float(value)
                if (
                    self.state.stop_freq is None
                    or abs(self.state.stop_freq - new_val) > 0.001
                ):
                    self.state.stop_freq = new_val
                    self._update_center_and_span_from_start_stop()
                    self.yak_communicator.publish_to_yak_and_trigger(
                        new_val,
                        self.yak_communicator.YAK_STOP_INPUT,
                        self.yak_communicator.YAK_STOP_TRIGGER,
                    )

            debug_logger(
                message="✅ The frequency settings did synchronize!", **_get_log_args()
            )

        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name}: {e}")
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🟢️️️🔴 Arrr, the code be capsized! The frequency logic has failed! The error be: {e}",
                    **_get_log_args(),
                )

    def _update_start_stop_from_center_span(self):
        current_function_name = inspect.currentframe().f_code.co_name

        if self.state.center_freq is not None and self.state.span_freq is not None:
            if self.state.span_freq <= 0:
                debug_logger(
                    message=f"❌ Error: Frequency span cannot be zero or negative. Value received: {self.state.span_freq}",
                    **_get_log_args(),
                )
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🟡 Warning! Invalid span value ({self.state.span_freq}) received. Ignoring update.",
                        **_get_log_args(),
                    )
                return

            new_start = round(self.state.center_freq - (self.state.span_freq / 2.0), 3)
            new_stop = round(self.state.center_freq + (self.state.span_freq / 2.0), 3)

            self.state._locked_state[
                f"{self.base_topic}/Settings/fields/start_freq_MHz/value"
            ] = True
            self.state._locked_state[
                f"{self.base_topic}/Settings/fields/stop_freq_MHz/value"
            ] = True

            self.state.start_freq = new_start
            self.state.stop_freq = new_stop

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🔁 Recalculated start/stop from center/span. Start: {new_start}, Stop: {new_stop}.",
                    **_get_log_args(),
                )

    def _update_center_and_span_from_start_stop(self):
        current_function_name = inspect.currentframe().f_code.co_name

        if self.state.start_freq is not None and self.state.stop_freq is not None:
            if self.state.start_freq < 0 or self.state.stop_freq < 0:
                debug_logger(
                    message=f"❌ Error: Start and stop frequencies cannot be negative. Start: {self.state.start_freq}, Stop: {self.state.stop_freq}.",
                    **_get_log_args(),
                )
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🟡 Warning! Invalid negative frequency values received. Ignoring update.",
                        **_get_log_args(),
                    )
                return

            if self.state.stop_freq < self.state.start_freq:
                debug_logger(
                    message=f"❌ Error: Stop frequency ({self.state.stop_freq}) cannot be less than start frequency ({self.state.start_freq}).",
                    **_get_log_args(),
                )
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🟡 Warning! Invalid start/stop combination received. Ignoring update.",
                        **_get_log_args(),
                    )
                return

            new_span = round(self.state.stop_freq - self.state.start_freq, 3)
            new_center = round(self.state.start_freq + (new_span / 2.0), 3)

            self.state._locked_state[
                f"{self.base_topic}/Settings/fields/span_freq_MHz/value"
            ] = True
            self.state._locked_state[
                f"{self.base_topic}/Settings/fields/center_freq_MHz/value"
            ] = True

            self.state.span_freq = new_span
            self.state.center_freq = new_center

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🔁 Recalculated center/span from start/stop. Center: {new_center}, Span: {new_span}.",
                    **_get_log_args(),
                )
