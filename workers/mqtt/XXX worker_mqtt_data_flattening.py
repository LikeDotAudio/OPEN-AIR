# workers/worker_mqtt_data_flattening.py
#
# A utility module to process and flatten nested MQTT payloads into a format
# suitable for display in a flat table or export to CSV. It buffers incoming
# messages until a complete set is received, then pivots the data.
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
# Version 20250825.151032.21

import os
import inspect
import orjson

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

# --- Global Scope Variables ---
LOCAL_DEBUG_ENABLE = False


class MqttDataFlattenerUtility:
    """
    Manages the buffering and flattening of incoming MQTT messages based on dynamic
    topic identifiers.
    """

    def __init__(self, print_to_gui_func):
        self._print_to_gui_console = print_to_gui_func
        self.data_buffer = {}
        self.current_class_name = self.__class__.__name__
        self.last_unique_identifier = None
        self.FLUSH_COMMAND = "FLUSH_BUFFER"

    def clear_buffer(self):
        """
        Clears the internal data buffer.
        """
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🔍 The data buffer has been wiped clean. A fresh start for our experiments!",
                **_get_log_args(),
            )
        self.data_buffer = {}
        self.last_unique_identifier = None

    def process_mqtt_message_and_pivot(
        self, topic: str, payload: str, topic_prefix: str
    ) -> list:
        """
        Processes a single MQTT message. It triggers flattening when it detects the
        start of a new data set based on the unique identifier.

        Args:
            topic (str): The MQTT topic of the message.
            payload (str): The JSON payload of the message.
            topic_prefix (str): The root topic to be used for filtering.

        Returns:
            list: A list of dictionaries representing the flattened, pivoted data,
                  or an empty list if not all messages have been received.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        # Check for the manual flush command
        if payload == self.FLUSH_COMMAND:
            if self.data_buffer:
                return self._flush_buffer()
            else:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message="🟢️️️🟡 Flush command received, but buffer is empty. Nothing to do.",
                        **_get_log_args(),
                    )
                return []

        try:
            data = orjson.loads(payload)

            # --- Corrected logic for 'Active' status check ---
            if (
                topic.endswith("/Active")
                and isinstance(data, dict)
                and data.get("value") == "false"
            ):
                debug_logger(
                    message=f"🟡 Skipping transaction for '{topic}' because 'Active' is false.",
                    **_get_log_args(),
                )
                self.clear_buffer()
                return []

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🟢️️️🔵 Received data for '{topic}'. Storing in buffer. Payload: {payload}",
                    **_get_log_args(),
                )

            # Extract the unique data set identifier (the second-to-last node)
            relative_topic = topic.replace(f"{topic_prefix}/", "", 1)
            identifier_path = relative_topic.rsplit("/", 1)[0]

            # This is the primary trigger for a new data set.
            if (
                self.last_unique_identifier
                and identifier_path != self.last_unique_identifier
            ):
                return self._flush_buffer(
                    new_topic=topic, new_data=data, new_identifier=identifier_path
                )

            # If this is the very first message, set the first key name and buffer it
            if self.last_unique_identifier is None:
                self.last_unique_identifier = identifier_path

            # Add the message to the buffer
            self.data_buffer[topic] = data

            return []

        except orjson.JSONDecodeError as e:
            debug_logger(
                message=f"❌ Error decoding JSON payload for topic '{topic}': {e}",
                **_get_log_args(),
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The JSON be a-sailing to its doom! The error be: {e}",
                    **_get_log_args(),
                )
            self.clear_buffer()
            return []
        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name}: {e}", **_get_log_args()
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Arrr, the code be capsized! The error be: {e}",
                    **_get_log_args(),
                )
            self.clear_buffer()
            return []

    def _flush_buffer(self, new_topic=None, new_data=None, new_identifier=None):
        """
        Processes and flattens the current buffer.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🟢 Processing buffer and commencing pivoting and flattening!",
                **_get_log_args(),
            )

        flattened_data = {}
        flattened_data["Parameter"] = self.last_unique_identifier

        for t, p in self.data_buffer.items():
            data_key = t.rsplit("/", 1)[-1]

            value = None
            if isinstance(p, dict) and "value" in p:
                value = p["value"]
            elif isinstance(p, str):
                value = p

            if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                value = value.strip('"')

            if value is not None:
                flattened_data[data_key] = value

        self.clear_buffer()

        if new_topic and new_data:
            self.data_buffer[new_topic] = new_data
            self.last_unique_identifier = new_identifier

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️✅ Behold! I have transmogrified the data! The final payload is below.",
                **_get_log_args(),
            )

        debug_logger(message=orjson.dumps(flattened_data, indent=2), **_get_log_args())
        return [flattened_data]
