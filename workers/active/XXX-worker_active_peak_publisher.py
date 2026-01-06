# workers/worker_active_peak_publisher.py
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251129  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 1  ## a running version number - incriments by one each time

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration


# A worker module that listens for marker frequency and amplitude outputs from the
# YAK repository and republishes the data to a new, deeply hierarchical topic
# structure based on the frequency (GHz down to 1s of kHz).
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
#
# Version 20251006.223430.3

import os
import inspect
import orjson
import threading
import re
import datetime
import math

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility

# --- Global Scope Variables (as per your instructions) ---
# NOTE: Version is updated to the current session time and revision 3
current_version = "20251006.223430.3"
# The hash calculation removes leading zeros, if any.
current_version_hash = 20251006 * 223430 * 3
current_file = f"{os.path.basename(__file__)}"
LOCAL_DEBUG_ENABLE = False

# --- Constants (No Magic Numbers) ---
# FIX: Using the single-level wildcard '+' to match the dynamic 'Marker_X' or 'Marker_X_freq' segment.
TOPIC_MARKER_PEAK_WILDCARD = (
    "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/Outputs/+/value"
)
TOPIC_MARKER_FREQ_WILDCARD = (
    "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/Outputs/+/value"
)
TOPIC_MEASUREMENTS_ROOT = "OPEN-AIR/measurements"
TOPIC_DELIMITER = "/"


class ActivePeakPublisher:
    """
    An event-driven worker that transforms flat marker data into a hierarchical
    topic structure based on frequency (GHz -> 100MHz -> 10MHz -> 1MHz -> 100kHz -> 10kHz -> 1kHz).
    """

    def __init__(self, mqtt_util: MqttControllerUtility):
        # Initializes the publisher and sets up subscriptions.
        current_function_name = inspect.currentframe().f_code.co_name

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🟢 Initializing the Active Peak Publisher. Ready to pivot the data!",
                **_get_log_args(),
            )

        self.mqtt_util = mqtt_util
        # Buffer to hold incomplete marker data (Peak or Freq only)
        # Key: Marker_ID (e.g., 'Marker_1'), Value: {'peak': float, 'freq_hz': float}
        self.marker_data_buffer = {}

        self._setup_subscriptions()
        debug_logger(
            message="✅ Active Peak Publisher is online and listening for marker data.",
            **_get_log_args(),
        )

    def _setup_subscriptions(self):
        # Subscribes to the wildcards for all marker peak and frequency values.
        self.mqtt_util.add_subscriber(
            TOPIC_MARKER_PEAK_WILDCARD, self._on_marker_message
        )
        self.mqtt_util.add_subscriber(
            TOPIC_MARKER_FREQ_WILDCARD, self._on_marker_message
        )

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Subscribed to both peak and frequency wildcards.",
                **_get_log_args(),
            )

    def _on_marker_message(self, topic, payload):
        # Primary callback to receive data, buffer it, and check for completeness.
        current_function_name = inspect.currentframe().f_code.co_name

        # Determine if it's a frequency or peak message
        # We look for the literal string 'freq' now, as the filter no longer guarantees a specific segment position.
        is_frequency = "freq" in topic

        # The Marker ID is the second-to-last part of the topic.
        # Example: .../Marker_1/value -> ['value', 'Marker_1', ...] -> Marker_1
        marker_id = topic.split(TOPIC_DELIMITER)[-2].replace("_freq", "")

        # Extract the value safely
        try:
            # 1. Decode the entire JSON payload to a Python dictionary
            payload_dict = orjson.loads(payload)
            # 2. Extract the string value (e.g., "-6.219589233E+01")
            value_str = payload_dict.get("value")

            # 3. Attempt to convert the string value to a float
            numeric_value = float(value_str)

        except (json.JSONDecodeError, ValueError, TypeError):
            # This block now captures errors from:
            # a) Invalid JSON structure (JSONDecodeError)
            # b) Missing 'value' key (TypeError/AttributeError from get("value") )
            # c) Unparsable number string (ValueError)
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"⚠️ Silent Skip: Unparsable payload '{payload}'.",
                    **_get_log_args(),
                )
            return

        # Initialize marker entry if it doesn't exist
        if marker_id not in self.marker_data_buffer:
            self.marker_data_buffer[marker_id] = {"peak": None, "freq_hz": None}

        # Update the buffer
        if is_frequency:
            self.marker_data_buffer[marker_id]["freq_hz"] = numeric_value
            data_type = "Frequency"
        else:
            self.marker_data_buffer[marker_id]["peak"] = numeric_value
            data_type = "Peak"

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"↔️ Buffered {data_type} for {marker_id}: {numeric_value}. Checking for pair...",
                **_get_log_args(),
            )

        # Check if both peak and frequency are now available
        buffer_entry = self.marker_data_buffer[marker_id]
        if buffer_entry["peak"] is not None and buffer_entry["freq_hz"] is not None:
            # Full data set for this marker is ready for publishing
            self._republish_to_hierarchical_topic(
                marker_id=marker_id,
                freq_hz=buffer_entry["freq_hz"],
                peak_dbm=buffer_entry["peak"],
            )
            # Clear the entry from the buffer
            del self.marker_data_buffer[marker_id]

    def _republish_to_hierarchical_topic(self, marker_id, freq_hz, peak_dbm):
        # Converts frequency in Hz to the required hierarchical topic structure and publishes.
        current_function_name = inspect.currentframe().f_code.co_name

        try:
            # Convert Hz to MHz for easier parsing (e.g., 612,345,000 Hz -> 612.345 MHz)
            freq_mhz = freq_hz / 1_000_000.0

            # --- Hierarchical Parsing ---

            # 1. Gigahertz (A)
            ghz = int(freq_mhz // 1000)
            freq_mhz_remainder = freq_mhz % 1000

            # 2. Hundreds of MHz (B)
            mhz_hundreds = int(freq_mhz_remainder // 100)
            mhz_remainder = freq_mhz_remainder % 100

            # 3. Tens of MHz (C)
            mhz_tens = int(mhz_remainder // 10)
            mhz_remainder = mhz_remainder % 10

            # 4. Ones of MHz (D)
            mhz_ones = int(mhz_remainder // 1)

            # 5. Kilohertz (E, F, G) - Convert remaining fraction to kHz
            khz_total = round((freq_mhz - int(freq_mhz)) * 1000.0, 0)

            khz_hundreds = int(khz_total // 100)
            khz_remainder = khz_total % 100

            khz_tens = int(khz_remainder // 10)
            khz_ones = int(khz_remainder % 10)

            # Final Frequency Breakdowns for the Topic Path: A/B/C/D/E/F/G
            # A: GHz
            # B: 100s of MHz
            # C: 10s of MHz
            # D: 1s of MHz
            # E: 100s of kHz
            # F: 10s of kHz
            # G: 1s of kHz

            topic_parts = [
                ghz,
                mhz_hundreds,
                mhz_tens,
                mhz_ones,
                khz_hundreds,
                khz_tens,
                khz_ones,
            ]

            # Join the parts to form the topic path
            topic_path = TOPIC_DELIMITER.join(map(str, topic_parts))
            full_topic = f"{TOPIC_MEASUREMENTS_ROOT}/{topic_path}"

            # Final Payload for the leaf node (G)
            final_payload = {
                "Marker": marker_id,
                "Peak_dBm": round(peak_dbm, 2),
                "Source_Freq_MHz": round(freq_mhz, 6),
                "Timestamp": datetime.datetime.now().isoformat(),
            }

            # Publish to the newly constructed hierarchical topic
            self.mqtt_util.publish_message(
                topic=full_topic,
                subtopic="",
                value=orjson.dumps(final_payload),
                retain=True,
            )

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🐐💾 Reposted {marker_id} data to hierarchical topic.",
                    **_get_log_args(),
                )
            debug_logger(
                message=f"✅ Reposted {marker_id} ({round(freq_mhz, 3)} MHz) to {full_topic}",
                **_get_log_args()(),
            )

        except Exception as e:
            debug_logger(
                message=f"❌ Error during hierarchical republishing for {marker_id}: {e}",
                **_get_log_args(),
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Arrr, the code be capsized in republishing! The error be: {e}",
                    **_get_log_args(),
                )
