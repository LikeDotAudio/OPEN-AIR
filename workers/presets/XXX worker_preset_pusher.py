# presets/XXX worker_preset_pusher.py
#
# A worker module to process a selected preset and push the corresponding
# SCPI commands via MQTT to configure the instrument.
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

import os
import inspect
import orjson
import time

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility

# --- Global Scope Variables ---
current_version = "20250919.231000.1"
current_version_hash = 20250919 * 231000 * 1
current_file = f"{os.path.basename(__file__)}"
LOCAL_DEBUG_ENABLE = False

HZ_TO_MHZ = 1_000_000

# --- MQTT Topic Constants (No Magic Numbers) ---
# Frequency
FREQ_START_INPUT = (
    "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/Input/start_freq/value"
)
FREQ_STOP_INPUT = "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/Input/stop_freq/value"
FREQ_TRIGGER = "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/scpi_details/Execute Command/trigger"

# Bandwidth
RBW_INPUT = "OPEN-AIR/yak/Bandwidth/set/Set_RBW/Input/hz_value/value"
RBW_TRIGGER = "OPEN-AIR/yak/Bandwidth/set/Set_RBW/scpi_details/Execute Command/trigger"
VBW_INPUT = "OPEN-AIR/yak/Bandwidth/set/Set_VBW/Input/hz_value/value"
VBW_TRIGGER = "OPEN-AIR/yak/Bandwidth/set/Set_VBW/scpi_details/Execute Command/trigger"

# Amplitude
AMP_TRIGGER = (
    "OPEN-AIR/yak/Amplitude/rig/rig_Ref_Level_dBm/scpi_details/Execute Command/trigger"
)
AMP_REF_LEVEL = "OPEN-AIR/yak/Amplitude/rig/rig_Ref_Level_dBm/Input/Ref_Level_dBm/value"
AMP_ATTENUATION = (
    "OPEN-AIR/yak/Amplitude/rig/rig_Ref_Level_dBm/Input/Attenuation_dB/value"
)
AMP_PREAMP = "OPEN-AIR/yak/Amplitude/rig/rig_Ref_Level_dBm/Input/Preamp_On/value"

# Trace Modes
TRACE_TRIGGER = (
    "OPEN-AIR/yak/Trace/rig/rig_All_trace_modes/scpi_details/Execute Command/trigger"
)
TRACE_MODE_1_INPUT = "OPEN-AIR/yak/Trace/rig/rig_All_trace_modes/Input/mode1/value"
TRACE_MODE_2_INPUT = "OPEN-AIR/yak/Trace/rig/rig_All_trace_modes/Input/mode2/value"
TRACE_MODE_3_INPUT = "OPEN-AIR/yak/Trace/rig/rig_All_trace_modes/Input/mode3/value"
TRACE_MODE_4_INPUT = "OPEN-AIR/yak/Trace/rig/rig_All_trace_modes/Input/mode4/value"


class PresetPusherWorker:
    """
    A worker class that takes a selected preset and pushes the settings to the instrument.
    """

    # Initializes the PresetPusherWorker.
    # This constructor takes an MQTT controller instance, which is used to publish
    # SCPI commands to the instrument based on selected presets.
    # Inputs:
    #     mqtt_controller (MqttControllerUtility): An instance of the MQTT controller utility.
    # Outputs:
    #     None.
    def __init__(self, mqtt_controller: MqttControllerUtility):
        """
        Initializes the worker with a shared MQTT controller instance.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        self.mqtt_controller = mqtt_controller
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🟢 The preset pusher has been summoned!", **_get_log_args()
            )

    # Configures the instrument based on a selected preset.
    # This method takes a list of preset values, maps them to specific instrument
    # settings (e.g., frequency, bandwidth, amplitude, trace modes), and then
    # publishes the corresponding SCPI commands via MQTT to configure the instrument.
    # Inputs:
    #     preset_values (list): A list of values for the selected preset.
    # Outputs:
    #     None.
    def Tune_to_preset(self, preset_values):
        """
        Executes a sequence of commands to configure the instrument based on a preset.

        Args:
            preset_values (list): A list of values for the selected preset.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🟢 Attuning the instrument to the selected preset. Ready the coils!",
                **_get_log_args(),
            )

        # Mapping the input list to readable variables
        keys = [
            "Preset_number",
            "Active",
            "FileName",
            "NickName",
            "Start",
            "Stop",
            "Center",
            "Span",
            "RBW",
            "VBW",
            "RefLevel",
            "Attenuation",
            "MaxHold",
            "HighSens",
            "PreAmp",
            "Trace1Mode",
            "Trace2Mode",
            "Trace3Mode",
            "Trace4Mode",
        ]
        preset_dict = dict(zip(keys, preset_values))

        # --- Mandatory: Set Start and Stop Frequencies ---
        try:

            start_freq_mhz = float(preset_dict.get("Start"))
            stop_freq_mhz = float(preset_dict.get("Stop"))

            # Apply the conversion from MHz to Hz
            self.mqtt_controller.publish_message(
                topic=FREQ_START_INPUT, subtopic="", value=start_freq_mhz * HZ_TO_MHZ
            )
            self.mqtt_controller.publish_message(
                topic=FREQ_STOP_INPUT, subtopic="", value=stop_freq_mhz * HZ_TO_MHZ
            )

            self.mqtt_controller.publish_message(
                topic=FREQ_TRIGGER, subtopic="", value=True
            )
            self.mqtt_controller.publish_message(
                topic=FREQ_TRIGGER, subtopic="", value=False
            )
            debug_logger(message="✅ Start/Stop frequencies set.")
        except Exception as e:
            debug_logger(message=f"❌ Error setting Start/Stop frequencies: {e}")
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The frequency setter is on the fritz! The error be: {e}",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                )

        # --- Conditional: Set RBW ---
        if (
            preset_dict.get("RBW") is not None
            and preset_dict.get("RBW").lower() != "null"
        ):
            self.mqtt_controller.publish_message(
                topic=RBW_INPUT, subtopic="", value=preset_dict.get("RBW")
            )
            self.mqtt_controller.publish_message(
                topic=RBW_TRIGGER, subtopic="", value=True
            )
            self.mqtt_controller.publish_message(
                topic=RBW_TRIGGER, subtopic="", value=False
            )
            debug_logger(message="✅ Resolution Bandwidth (RBW) set.")

        # --- Conditional: Set VBW ---
        if (
            preset_dict.get("VBW") is not None
            and preset_dict.get("VBW").lower() != "null"
        ):
            self.mqtt_controller.publish_message(
                topic=VBW_INPUT, subtopic="", value=preset_dict.get("VBW")
            )
            self.mqtt_controller.publish_message(
                topic=VBW_TRIGGER, subtopic="", value=True
            )
            self.mqtt_controller.publish_message(
                topic=VBW_TRIGGER, subtopic="", value=False
            )
            debug_logger(message="✅ Video Bandwidth (VBW) set.")

        # --- Conditional: Set Amplitude Rig ---
        ref_level = preset_dict.get("RefLevel")
        attenuation = preset_dict.get("Attenuation")
        preamp = preset_dict.get("PreAmp")
        if all(
            val is not None and val.lower() != "null"
            for val in [ref_level, attenuation, preamp]
        ):
            self.mqtt_controller.publish_message(
                topic=AMP_REF_LEVEL, subtopic="", value=ref_level
            )
            self.mqtt_controller.publish_message(
                topic=AMP_ATTENUATION, subtopic="", value=attenuation
            )
            self.mqtt_controller.publish_message(
                topic=AMP_PREAMP, subtopic="", value=preamp
            )
            self.mqtt_controller.publish_message(
                topic=AMP_TRIGGER, subtopic="", value=True
            )
            self.mqtt_controller.publish_message(
                topic=AMP_TRIGGER, subtopic="", value=False
            )
            debug_logger(
                message="✅ Amplitude settings (RefLevel, Attenuation, Preamp) set."
            )

        # --- Conditional: Set Trace Modes ---
        trace_modes = [preset_dict.get(f"Trace{i}Mode") for i in range(1, 5)]
        if all(val is not None and val.lower() != "null" for val in trace_modes):
            self.mqtt_controller.publish_message(
                topic=TRACE_MODE_1_INPUT, subtopic="", value=trace_modes[0]
            )
            self.mqtt_controller.publish_message(
                topic=TRACE_MODE_2_INPUT, subtopic="", value=trace_modes[1]
            )
            self.mqtt_controller.publish_message(
                topic=TRACE_MODE_3_INPUT, subtopic="", value=trace_modes[2]
            )
            self.mqtt_controller.publish_message(
                topic=TRACE_MODE_4_INPUT, subtopic="", value=trace_modes[3]
            )
            self.mqtt_controller.publish_message(
                topic=TRACE_TRIGGER, subtopic="", value=True
            )
            self.mqtt_controller.publish_message(
                topic=TRACE_TRIGGER, subtopic="", value=False
            )
            debug_logger(message="✅ Trace modes set.")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️✅ The tuning sequence is complete! All command triggers have been sent.",
                **_get_log_args(),
            )


if __name__ == "__main__":
    # Mock classes for standalone testing
    class MockMqttUtility:
        def publish_message(self, topic: str, subtopic: str, value, retain=False):
            full_topic = f"{topic}/{subtopic}" if subtopic else topic
            print(f"Mock publish: {full_topic} -> {value}")

    mock_mqtt_util = MockMqttUtility()
    worker = PresetPusherWorker(mqtt_controller=mock_mqtt_util)

    # Example preset data (from your log)
    example_preset_values = [
        "PRESET_003",
        "true",
        "34MON.STA",
        "34MON",
        "590",
        "650",
        "620",
        "60",
        "30000",
        "null",
        "null",
        "-50",
        "null",
        "null",
        "Write",
        "MAXhold",
        "MINhold",
        "null",
        "",
    ]

    print("\n--- Testing Tune_to_preset with example data ---")
    worker.Tune_to_preset(preset_values=example_preset_values)