# workers/markers/worker_marker_peak_re_publisher.py
#
# This worker listens to the immediate output of the NAB marker command (Marker_1/value, etc.)
# and republishes the received peak value to the final markers repository location.
# It is instantiated with the starting device ID of the current batch to correctly map outputs.
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
# Version 20251213.120000.44

import os
import inspect
import orjson
import threading
import re
import time

# --- Module Imports ---
from workers.logger.logger import debug_logger

# from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility

# --- Global Scope Variables ---
Current_Date = 20251213
Current_Time = 120000
Current_iteration = 44

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration
current_file = f"{os.path.basename(__file__)}"


# --- MQTT Topic Constants ---
TOPIC_MARKERS_ROOT = "OPEN-AIR/measurements"
TOPIC_MARKER_NAB_OUTPUT_WILDCARD = (
    "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/Outputs/Marker_*/value"
)
NUMBER_OF_MARKERS = 6


class MarkerPeakPublisher:
    """
    Handles subscriptions to the immediate NAB marker output and republishes the values
    to the correct final Device-ID/Peak topics based on a provided starting device ID.
    """

    def __init__(self, mqtt_util: MqttControllerUtility, starting_device_id: str):
        current_function_name = inspect.currentframe().f_code.co_name

        debug_logger(
            message=f"🟢️️️🟢 Initializing Peak Publisher for batch starting with {starting_device_id}. STARTING MAP GENERATION.",
            **_get_log_args(),
        )

        self.mqtt_util = mqtt_util
        self.starting_device_id = starting_device_id

        self.marker_to_device_map = self._generate_device_map(starting_device_id)
        debug_logger(
            message=f"🟢️️️🔍 Generated Map: {self.marker_to_device_map}",
            **_get_log_args(),
        )

        # Register Subscription
        self._setup_subscriptions()

        debug_logger(
            message=f"✅ Peak Publisher for {starting_device_id} is active and ready to catch peak values."
        )

    def _generate_device_map(self, start_id: str) -> dict:
        """
        Calculates the next 5 device IDs and maps Marker_1..Marker_6 to them.
        Assumes ID format is 'Device-###'.
        """
        device_map = {}
        # Extract the number from the starting device ID (e.g., 025 from Device-025)
        match = re.search(r"Device-(\d+)", start_id)
        if not match:
            debug_logger(
                message=f"❌ Error: Invalid starting Device ID format: {start_id}"
            )
            return {}

        start_num = int(match.group(1))

        for i in range(NUMBER_OF_MARKERS):
            current_num = start_num + i
            # Format the number back to three digits (e.g., 025)
            device_id = f"Device-{current_num:03d}"
            marker_key = f"Marker_{i + 1}"
            device_map[marker_key] = device_id

        return device_map

    def _setup_subscriptions(self):
        """
        Subscribes to the specific NAB Marker outputs.
        """
        # We subscribe to the wildcard and rely on the callback to handle the topic match.
        self.mqtt_util.add_subscriber(
            TOPIC_MARKER_NAB_OUTPUT_WILDCARD, self._on_nab_output_and_republish_peak
        )

    def _on_nab_output_and_republish_peak(self, topic, payload):
        """
        Listens to the NAB query results (Marker_X/value), logs the result,
        and republishes the peak value to the final Device-ID/Peak topic.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        debug_logger(
            message=f"🐐🟢 PUBLISHER HANDLER FIRED for topic: {topic}",
            file=current_file,
            version=current_version,
            function=current_function_name,
        )

        try:
            # 1. Extract Marker ID and Peak Value
            marker_id = topic.split("/")[-2]  # e.g., "Marker_1"
            device_id = self.marker_to_device_map.get(marker_id)
            final_peak_topic = f"{TOPIC_MARKERS_ROOT}/{device_id}/Peak"

            # Safely extract peak value
            try:
                # Value is stored as a JSON string by YakRxManager
                peak_value = orjson.loads(payload).get("value")
            except (json.JSONDecodeError, AttributeError):
                peak_value = payload  # Fallback to raw payload

            # 2. Validation and Publishing
            try:
                # Attempt to convert to float. This will fail if the value is 'nan' or 'ERROR'.
                float_peak_value = float(peak_value)

                # Republishing - Publish to the final repo path
                if device_id:
                    self.mqtt_util.publish_message(
                        final_peak_topic, "", float_peak_value, retain=True
                    )

                    debug_logger(
                        message=f"🐐💾 REPUBLISH SUCCESS: {device_id} ({marker_id}) peak: {float_peak_value} dBm. Final Topic: {final_peak_topic}",
                        file=current_file,
                        version=current_version,
                        function=current_function_name,
                    )
                else:
                    debug_logger(
                        message=f"🐐🟡 REPUBLISH WARNING: Peak received for {marker_id} but no Device-ID found in batch map.",
                        file=current_file,
                        version=current_version,
                        function=current_function_name,
                    )

            except ValueError:
                # This block handles "nan" or non-numeric strings, which is your requested error spot.
                error_message = "🔴 ERROR: Peak Value Invalid"
                self.mqtt_util.publish_message(
                    final_peak_topic, "", error_message, retain=True
                )

                debug_logger(
                    message=f"❌ REPUBLISH ERROR: Peak Value '{peak_value}' for {device_id} failed conversion. Published Error Status.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                )

        except Exception as e:
            # General failure protection
            # Find the first device ID in the map for error context
            first_device_id = next(
                iter(self.marker_to_device_map.values()), "UNKNOWN_DEVICE"
            )
            final_peak_topic = f"{TOPIC_MARKERS_ROOT}/{first_device_id}/Peak"
            self.mqtt_util.publish_message(
                final_peak_topic, "", "CRITICAL_ERROR", retain=True
            )

            debug_logger(
                message=f"❌ Critical Error in Peak Publisher for {first_device_id}: {e}"
            )
            debug_logger(
                message=f"❌ CRITICAL FAILURE in Publisher Flow. Error: {e}",
                file=current_file,
                version=current_version,
                function=current_function_name,
            )
