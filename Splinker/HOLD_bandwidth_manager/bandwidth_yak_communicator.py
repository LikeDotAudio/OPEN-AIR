# managers/bandwidth_manager/bandwidth_yak_communicator.py
#
# This file (bandwidth_yak_communicator.py) handles communication with the YAK repository for bandwidth settings, including publishing RBW, VBW, and sweep time values.
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

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.logger.log_utils import _get_log_args

## from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility
from .bandwidth_state import BandwidthState

LOCAL_DEBUG_ENABLE = False


class BandwidthYakCommunicator:
    """Handles communication with the YAK repository for bandwidth settings."""

    HZ_TO_MHZ = 1_000_000.0
    YAK_BASE = "OPEN-AIR/yak/Bandwidth"

    YAK_UPDATE_TOPIC = (
        f"{YAK_BASE}/nab/NAB_bandwidth_settings/scpi_details/Execute Command/trigger"
    )
    YAK_RBW_TRIGGER = f"{YAK_BASE}/set/Set_RBW/scpi_details/Execute Command/trigger"
    YAK_SWEEP_TIME_TRIGGER = (
        f"{YAK_BASE}/set/Set_Sweep_time/scpi_details/Execute Command/trigger"
    )
    YAK_VBW_TRIGGER = f"{YAK_BASE}/set/Set_VBW/scpi_details/Execute Command/trigger"
    YAK_VBW_AUTO_ON_TRIGGER = f"{YAK_BASE}/set/do_Video_Bandwidth_Auto_ON/scpi_details/Execute Command/trigger"
    YAK_VBW_AUTO_OFF_TRIGGER = f"{YAK_BASE}/set/do_Video_Bandwidth_Auto_OFF/scpi_details/Execute Command/trigger"

    YAK_RBW_INPUT = f"{YAK_BASE}/set/Set_RBW/Input/hz_value/value"
    YAK_SWEEP_TIME_INPUT = f"{YAK_BASE}/set/Set_Sweep_time/Input/s_value/value"
    YAK_VBW_INPUT = f"{YAK_BASE}/set/Set_VBW/Input/hz_value/value"

    YAK_NAB_OUTPUTS = {
        "RBW_Hz/value": "Settings/fields/Resolution Bandwidth/fields/RBW/value",
        "VBW_Hz/value": "Settings/fields/Video Bandwidth/fields/vbw_MHz/value",
        "VBW_Auto_On/value": "Settings/fields/Video Bandwidth/fields/VBW_Automatic/options/ON/selected",
        "Continuous_Mode_On/value": "Settings/fields/Sweep_Mode/options/Continuous/selected",
        "Sweep_Time_s/value": "Settings/fields/Sweep_time_s/value",
    }

    def __init__(self, mqtt_controller, state: BandwidthState):
        ## self.mqtt_controller = mqtt_controller
        self.state = state
        self.base_topic = self.state.base_topic

    def publish_rbw_and_trigger(self, value_mhz):
        value_hz = int(round(value_mhz * self.HZ_TO_MHZ))
        self.publish_to_yak_and_trigger(
            value=value_hz,
            input_topic=self.YAK_RBW_INPUT,
            trigger_topic=self.YAK_RBW_TRIGGER,
        )

    def publish_sweep_time_and_trigger(self, value_s):
        self.publish_to_yak_and_trigger(
            value=float(value_s),
            input_topic=self.YAK_SWEEP_TIME_INPUT,
            trigger_topic=self.YAK_SWEEP_TIME_TRIGGER,
        )

    def publish_vbw_and_trigger(self, value_mhz):
        value_hz = int(round(value_mhz * self.HZ_TO_MHZ))
        self.publish_to_yak_and_trigger(
            value=value_hz,
            input_topic=self.YAK_VBW_INPUT,
            trigger_topic=self.YAK_VBW_TRIGGER,
        )

    def publish_vbw_auto_and_trigger(self, is_auto_on):
        trigger_topic = (
            self.YAK_VBW_AUTO_ON_TRIGGER
            if is_auto_on
            else self.YAK_VBW_AUTO_OFF_TRIGGER
        )
        ## self.mqtt_controller.publish_message(topic=trigger_topic, subtopic="", value=True, retain=False)
        time.sleep(0.01)
        ## self.mqtt_controller.publish_message(topic=trigger_topic, subtopic="", value=False, retain=False)
        self.update_all_from_device()

    def publish_to_yak_and_trigger(self, value, input_topic, trigger_topic):
        ## self.mqtt_controller.publish_message(topic=input_topic, subtopic="", value=value, retain=True)
        ## self.mqtt_controller.publish_message(topic=trigger_topic, subtopic="", value=True, retain=False)
        time.sleep(0.01)
        ## self.mqtt_controller.publish_message(topic=trigger_topic, subtopic="", value=False, retain=False)
        self.update_all_from_device()

    def update_all_from_device(self):
        ## self.mqtt_controller.publish_message(topic=self.YAK_UPDATE_TOPIC, subtopic="", value=True, retain=False)
        time.sleep(0.01)
        ## self.mqtt_controller.publish_message(topic=self.YAK_UPDATE_TOPIC, subtopic="", value=False, retain=False)

    def process_yak_output(self, topic, payload):
        try:
            yak_suffix = topic.split("/Outputs/")[1]
            gui_suffix = self.YAK_NAB_OUTPUTS.get(yak_suffix)
            if not gui_suffix:
                return

            try:
                raw_value = orjson.loads(payload).get("value", payload)
            except (orjson.JSONDecodeError, TypeError):
                raw_value = payload

            full_gui_topic = f"{self.base_topic}/{gui_suffix}"
            if full_gui_topic in self.state._locked_state:
                self.state._locked_state[full_gui_topic] = True

            if "RBW_Hz" in yak_suffix:
                final_value_mhz = float(raw_value) / self.HZ_TO_MHZ
                self.state.rbw_value = final_value_mhz
                self._publish_update(topic_suffix=gui_suffix, value=final_value_mhz)
            elif "VBW_Hz" in yak_suffix:
                final_value_mhz = float(raw_value) / self.HZ_TO_MHZ
                self.state.vbw_value = final_value_mhz
                self._publish_update(topic_suffix=gui_suffix, value=final_value_mhz)
            elif "VBW_Auto_On" in yak_suffix:
                is_on = str(raw_value).strip() == "1"
                self._publish_update(
                    topic_suffix="Settings/fields/Video Bandwidth/fields/VBW_Automatic/options/ON/selected",
                    value=is_on,
                )
                self._publish_update(
                    topic_suffix="Settings/fields/Video Bandwidth/fields/VBW_Automatic/options/OFF/selected",
                    value=not is_on,
                )
            elif "Continuous_Mode_On" in yak_suffix:
                is_on = str(raw_value).strip() == "1"
                self._publish_update(
                    topic_suffix="Settings/fields/Sweep_Mode/options/Continuous/selected",
                    value=is_on,
                )
                self._publish_update(
                    topic_suffix="Settings/fields/Sweep_Mode/options/Single/selected",
                    value=not is_on,
                )
            elif "Sweep_Time_s" in yak_suffix:
                final_value = float(raw_value)
                self.state.sweep_time_value = final_value
                self._publish_update(topic_suffix=gui_suffix, value=final_value)
        except Exception as e:
            debug_logger(
                message=f"❌ Error processing YAK output for {topic}: {e}",
                **_get_log_args(),
            )

    def _publish_update(self, topic_suffix, value):
        full_topic = f"{self.base_topic}/{topic_suffix}"
        rounded_value = round(float(value), 6)
        self.mqtt_controller.publish_message(
            topic=full_topic, subtopic="", value=rounded_value, retain=False
        )
