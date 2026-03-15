# mqtt/XXX worker_mqtt_data_flattening.py
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
# Version 20250821.200641.1

import os
import inspect
import orjson

# --- Module Imports ---
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger


# --- Global Scope Variables ---
LOCAL_DEBUG = True   


class MqttDataFlattenerUtility:
    """
    Manages the buffering and flattening of incoming MQTT messages based on dynamic
    topic identifiers.
    """

    # Initializes the MqttDataFlattenerUtility.
    # This sets up an empty data buffer and state variables for tracking unique identifiers,
    # which are used to manage incoming MQTT messages and trigger the flattening process.
    # Inputs:
    #     print_to_gui_func (function): A function to print messages to the GUI console.
    # Outputs:
    #     None.
    def __init__(self, print_to_gui_func):
        self._print_to_gui_console = print_to_gui_func
        self.data_buffer = {}
        self.current_class_name = self.__class__.__name__
        self.last_unique_identifier = None
        self.FLUSH_COMMAND = "FLUSH_BUFFER"

    # Clears the internal data buffer.
    # This method empties the `data_buffer` and resets the `last_unique_identifier`,
    # preparing the utility for processing a new set of incoming MQTT messages.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def clear_buffer(self):
        """
        Clears the internal data buffer.
        """
        if LOCAL_DEBUG:
            logger.debug("🟢️️️🔍 The data buffer has been wiped clean. A fresh start for our experiments!")
        self.data_buffer = {}
        self.last_unique_identifier = None

    # Processes an incoming MQTT message, buffering it and triggering data flattening when a new data set is detected.
    # This method stores messages in an internal buffer, identifies unique data set identifiers
    # from the topic, and, upon detecting a new data set or a manual flush command,
    # flushes the buffer to produce flattened, pivoted data.
    # Inputs:
    #     topic (str): The MQTT topic of the incoming message.
    #     payload (str): The JSON payload of the message.
    #     topic_prefix (str): The root topic used for filtering.
    # Outputs:
    #     list: A list of dictionaries representing the flattened, pivoted data, or an empty list.
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
                if LOCAL_DEBUG:
                    logger.debug("🟢️️️🟡 Flush command received, but buffer is empty. Nothing to do.")
                return []

        try:
            data = orjson.loads(payload)

            # --- Corrected logic for 'Active' status check ---
            if (
                topic.endswith("/Active")
                and isinstance(data, dict)
                and data.get("value") == "false"
            ):
                if LOCAL_DEBUG: logger.debug(f"🟡 Skipping transaction for '{topic}' because 'Active' is false.")
                self.clear_buffer()
                return []

            if LOCAL_DEBUG:
                logger.debug(f"🟢️️️🔵 Received data for '{topic}'. Storing in buffer. Payload: {payload}")

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
            logger.error(f"❌ Error decoding JSON payload for topic '{topic}': {e}")
            if LOCAL_DEBUG:
                logger.error(f"❌ The JSON be a-sailing to its doom! The error be: {e}")
            self.clear_buffer()
            return []
        except Exception as e:
            logger.exception("❌ Error in {current_function_name}")
            if LOCAL_DEBUG:
                logger.exception("❌ Arrr, the code be capsized! The error be")
            self.clear_buffer()
            return []

    # Processes and flattens the current data buffer.
    # This method takes the buffered MQTT messages, extracts key-value pairs,
    # and transforms them into a flattened, pivoted list of dictionaries,
    # suitable for display in a table or export to CSV.
    # Inputs:
    #     new_topic (str, optional): The topic of the new message that triggered the flush.
    #     new_data: The data from the new message.
    #     new_identifier (str, optional): The unique identifier of the new data set.
    # Outputs:
    #     list: A list of dictionaries representing the flattened, pivoted data.
    def _flush_buffer(self, new_topic=None, new_data=None, new_identifier=None):
        """
        Processes and flattens the current buffer.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if LOCAL_DEBUG:
            logger.debug("🟢️️️🟢 Processing buffer and commencing pivoting and flattening!")

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

        if LOCAL_DEBUG:
            logger.success("🟢️️️✅ Behold! I have transmogrified the data! The final payload is below.")

        if LOCAL_DEBUG: logger.debug(orjson.dumps(flattened_data, indent=2))
        return [flattened_data]