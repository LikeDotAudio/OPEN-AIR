# managers/bandwidth_manager/bandwidth_presets.py
#
## This file (bandwidth_presets.py) handles preset logic for bandwidth settings, including RBW and VBW, and applies them via MQTT.
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


import os

## from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility
from .bandwidth_state import BandwidthState
from .bandwidth_yak_communicator import BandwidthYakCommunicator
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.logger.log_utils import _get_log_args

LOCAL_DEBUG_ENABLE = False


class BandwidthPresets:
    """Handles preset logic for bandwidth settings."""

    TOPIC_RBW_PRESET_WILDCARD = "OPEN-AIR/configuration/instrument/bandwidth/Settings/fields/Resolution Bandwidth/fields/Resolution Band Width/options/+/value"
    TOPIC_VBW_PRESET_WILDCARD = "OPEN-AIR/configuration/instrument/bandwidth/Settings/fields/Video Bandwidth/fields/Video Band Width /options/+/value"

    TOPIC_RBW_UNITS_WILDCARD = "OPEN-AIR/configuration/instrument/bandwidth/Settings/fields/Resolution Bandwidth/fields/Resolution Band Width/options/+/units"
    TOPIC_VBW_UNITS_WILDCARD = "OPEN-AIR/configuration/instrument/bandwidth/Settings/fields/Video Bandwidth/fields/Video Band Width /options/+/units"

    def __init__(
        self,
        mqtt_controller,
        state: BandwidthState,
        yak_communicator: BandwidthYakCommunicator,
    ):
        ## self.mqtt_controller = mqtt_controller
        self.state = state
        self.yak_communicator = yak_communicator
        self.base_topic = self.state.base_topic

    def handle_preset_message(self, topic, value):
        def _get_option_number(t):
            try:
                return int(t.split("/")[-2])
            except (ValueError, IndexError):
                return None

        if "Resolution Bandwidth/fields/Resolution Band Width/options" in topic:
            if topic.endswith("/value"):
                opt_num = _get_option_number(topic)
                if opt_num is not None:
                    self.state.rbw_preset_values[opt_num] = float(value)
            elif topic.endswith("/units"):
                opt_num = _get_option_number(topic)
                if opt_num is not None:
                    self.state.rbw_preset_units[opt_num] = str(value)
            elif topic.endswith("/selected") and str(value).lower() == "true":
                self.apply_preset(
                    topic,
                    self.state.rbw_preset_values,
                    self.state.rbw_preset_units,
                    "Settings/fields/Resolution Bandwidth/fields/RBW/value",
                    is_rbw=True,
                )
            return True

        if "Video Bandwidth/fields/Video Band Width /options" in topic:
            if topic.endswith("/value"):
                opt_num = _get_option_number(topic)
                if opt_num is not None:
                    self.state.vbw_preset_values[opt_num] = float(value)
            elif topic.endswith("/units"):
                opt_num = _get_option_number(topic)
                if opt_num is not None:
                    self.state.vbw_preset_units[opt_num] = str(value)
            elif topic.endswith("/selected") and str(value).lower() == "true":
                self.apply_preset(
                    topic,
                    self.state.vbw_preset_values,
                    self.state.vbw_preset_units,
                    "Settings/fields/Video Bandwidth/fields/vbw_MHz/value",
                    is_rbw=False,
                )
            return True

        return False

    def apply_preset(
        self, topic, preset_value_map, preset_unit_map, target_suffix, is_rbw: bool
    ):
        try:
            option_number = int(topic.split("/")[-2])
            raw_value = preset_value_map.get(option_number)
            unit_string = preset_unit_map.get(option_number)

            if raw_value is not None and unit_string is not None:
                multiplier = self.state.get_multiplier(unit_string=unit_string)
                final_value_hz = raw_value * multiplier
                new_value_mhz = final_value_hz / self.yak_communicator.HZ_TO_MHZ

                full_target_topic = f"{self.base_topic}/{target_suffix}"
                if full_target_topic in self.state._locked_state:
                    self.state._locked_state[full_target_topic] = True

                self.yak_communicator._publish_update(
                    topic_suffix=target_suffix, value=new_value_mhz
                )
                ## self.mqtt_controller.publish_message(topic=topic, subtopic="", value=True, retain=False)

                yak_input = (
                    self.yak_communicator.YAK_RBW_INPUT
                    if is_rbw
                    else self.yak_communicator.YAK_VBW_INPUT
                )
                yak_trigger = (
                    self.yak_communicator.YAK_RBW_TRIGGER
                    if is_rbw
                    else self.yak_communicator.YAK_VBW_TRIGGER
                )
                self.yak_communicator.publish_to_yak_and_trigger(
                    value=final_value_hz,
                    input_topic=yak_input,
                    trigger_topic=yak_trigger,
                )
            else:
                debug_logger(
                    message=f"❌ Error: Preset data missing for option {option_number}.",
                    **_get_log_args(),
                )
                ## self.mqtt_controller.publish_message(topic=topic, subtopic="", value=False, retain=False)
                self.yak_communicator.update_all_from_device()
        except Exception as e:
            debug_logger(message=f"❌ Error applying preset: {e}", **_get_log_args())
