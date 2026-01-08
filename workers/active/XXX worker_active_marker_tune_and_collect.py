# active/XXX worker_active_marker_tune_and_collect.py
#
# This worker listens for a start command and then continuously loops through all
# markers from the repository, gets their peak values from the instrument, and
# updates the repository with the new peak data.
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
import pathlib
import threading
import time

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.mqtt.worker_mqtt_controller_util import MqttControllerUtility


# --- Global Scope Variables ---
current_version = "20251006.225130.6"
# The hash calculation drops the leading zero from the hour (e.g., 083015 becomes 83015).
current_version_hash = 20251006 * 225130 * 6
current_file = f"{os.path.basename(__file__)}"
HZ_TO_MHZ = 1_000_000
LOCAL_DEBUG_ENABLE = False


# --- NEW CONSTANT: Frequency Buffer (in MHz) ---
BUFFER_START_STOP_MHZ = 0.1

# --- MQTT Topic Constants (UPDATED FOR /IDENTITY NESTING) ---
# Control Topics
TOPIC_START_STOP = (
    "OPEN-AIR/configuration/Start-Stop-Pause/Buttons/options/START/selected"
)

# Marker Repository Topics
TOPIC_MARKERS_ROOT = "OPEN-AIR/repository/markers"
TOPIC_TOTAL_DEVICES = f"{TOPIC_MARKERS_ROOT}/total_devices"
TOPIC_MIN_FREQ = f"{TOPIC_MARKERS_ROOT}/min_frequency_mhz"
TOPIC_MAX_FREQ = f"{TOPIC_MARKERS_ROOT}/max_frequency_mhz"

# FIX: Update topic to search for frequency inside the /IDENTITY node
TOPIC_DEVICE_FREQ_WILDCARD = f"{TOPIC_MARKERS_ROOT}/+/IDENTITY/FREQ_MHZ"


# YAK Frequency Topics
TOPIC_FREQ_START_INPUT = (
    "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/Input/start_freq/value"
)
TOPIC_FREQ_STOP_INPUT = (
    "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/Input/stop_freq/value"
)
TOPIC_FREQ_TRIGGER = "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/scpi_details/Execute Command/trigger"

# YAK Marker Placement Topics
TOPIC_MARKER_PLACE_BASE = "OPEN-AIR/yak/Markers/beg/Beg_Place_All_markers/Input"
TOPIC_MARKER_PLACE_TRIGGER = "OPEN-AIR/yak/Markers/beg/Beg_Place_All_markers/scpi_details/Execute Command/trigger"

# YAK Marker Value Retrieval (NAB) Topics
TOPIC_MARKER_NAB_TRIGGER = "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/scpi_details/Execute Command/trigger"
TOPIC_MARKER_NAB_OUTPUT_WILDCARD = (
    "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/Outputs/Marker_*/value"
)


class MarkerGoGetterWorker:
    """
    A worker that, when started, continuously fetches peak values for all markers.
    """

    # Initializes the MarkerGoGetterWorker.
    # This sets up the worker's initial state, including its MQTT utility, threading events for
    # controlling the processing loop, and data structures for storing marker information.
    # Inputs:
    #     mqtt_util (MqttControllerUtility): The MQTT utility for publishing and subscribing.
    # Outputs:
    #     None.
    def __init__(self, mqtt_util: MqttControllerUtility):
        """
        Initializes the worker, sets up state variables, and subscribes to topics.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🟢 Initializing the tireless Marker Go-Getter!",
                **_get_log_args(),
            )

        self.mqtt_util = mqtt_util
        self.processing_thread = None
        self.stop_event = threading.Event()

        # State variables populated by MQTT
        self.total_devices = 0
        self.min_frequency_mhz = 0.0
        self.max_frequency_mhz = 0.0
        self.marker_frequencies = {}

        # New variables to track frequency state for conditional updates
        self.last_min_freq = None
        self.last_max_freq = None
        self.first_run = True

        # For flow control signaling
        self.peaks_received_event = threading.Event()

        self._setup_subscriptions()

    # Sets up all necessary MQTT subscriptions for the worker.
    # This method subscribes to topics for starting and stopping the worker, as well as topics
    # that provide data from the marker repository and instrument.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _setup_subscriptions(self):
        """
        Subscribes to all topics required for operation.
        """
        self.mqtt_util.add_subscriber(TOPIC_START_STOP, self._handle_start_stop)
        self.mqtt_util.add_subscriber(TOPIC_TOTAL_DEVICES, self._on_marker_data_update)
        self.mqtt_util.add_subscriber(TOPIC_MIN_FREQ, self._on_marker_data_update)
        self.mqtt_util.add_subscriber(TOPIC_MAX_FREQ, self._on_marker_data_update)
        # FIX: Subscribes to the new wildcard topic for marker frequency
        self.mqtt_util.add_subscriber(
            TOPIC_DEVICE_FREQ_WILDCARD, self._on_marker_data_update
        )

        # Subscribe to the NAB outputs directly to set the flow control event.
        # FIXED: This method was missing but is now the target of the NAB outputs.
        self.mqtt_util.add_subscriber(
            TOPIC_MARKER_NAB_OUTPUT_WILDCARD, self._on_peak_update_for_event_set
        )

        debug_logger(
            message="✅ Go-Getter is now listening for commands and marker data."
        )

    # Callback function triggered by peak value updates from the instrument.
    # This method sets a threading event to signal that new peak data has been received,
    # allowing the main processing loop to proceed.
    # Inputs:
    #     topic (str): The MQTT topic the message was received on.
    #     payload (str): The message payload.
    # Outputs:
    #     None.
    def _on_peak_update_for_event_set(self, topic, payload):
        """
        A placeholder method to satisfy the subscription. In a non-mock setup,
        this would signal a threading event to continue the main processing loop.
        """
        self.peaks_received_event.set()

    # Updates the worker's internal state based on data from the marker repository.
    # This callback processes incoming MQTT messages containing information about markers,
    # such as the total number of devices and their frequencies.
    # Inputs:
    #     topic (str): The MQTT topic the message was received on.
    #     payload (str): The message payload.
    # Outputs:
    #     None.
    def _on_marker_data_update(self, topic, payload):
        """
        Callback to update internal state from the markers repository.
        """
        try:
            # Safely attempt to extract value from a potential JSON payload
            try:
                value = orjson.loads(payload).get("value")
            except (orjson.JSONDecodeError, AttributeError):
                value = payload  # Fallback to raw payload if not a JSON object

            if topic == TOPIC_TOTAL_DEVICES:
                self.total_devices = int(value)
            elif topic == TOPIC_MIN_FREQ:
                self.min_frequency_mhz = float(value)
            elif topic == TOPIC_MAX_FREQ:
                self.max_frequency_mhz = float(value)
            # FIX: Check if the topic structure matches a device frequency update inside /IDENTITY
            elif topic.endswith("/IDENTITY/FREQ_MHZ"):
                topic_parts = topic.split("/")
                # The Device-XXX ID is the third part from the end: .../Device-XXX/IDENTITY/FREQ_MHZ
                if len(topic_parts) >= 4 and topic_parts[-3].startswith("Device-"):
                    device_id = topic_parts[-3]
                    self.marker_frequencies[device_id] = float(value)
        except (orjson.JSONDecodeError, ValueError, TypeError) as e:
            debug_logger(
                message=f"🟡 Warning: Could not process marker data update from topic '{topic}': {e}"
            )

    # Handles start and stop commands for the worker.
    # This method starts or stops the main processing loop in a separate thread based on
    # the received command.
    # Inputs:
    #     topic (str): The MQTT topic the command was received on.
    #     payload (str): The command payload ('true' for start, 'false' for stop).
    # Outputs:
    #     None.
    def _handle_start_stop(self, topic, payload):
        """
        Starts or stops the main processing loop in a separate thread.
        """
        try:
            # Safely extract boolean value
            try:
                is_start_command = (
                    str(orjson.loads(payload).get("value")).lower() == "true"
                )
            except (orjson.JSONDecodeError, AttributeError):
                is_start_command = str(payload).lower() == "true"

            if is_start_command and (
                self.processing_thread is None or not self.processing_thread.is_alive()
            ):
                debug_logger(
                    message="🟢 START command received. Beginning marker peak acquisition loop."
                )
                self.stop_event.clear()
                # Reset first run flag when starting a new sequence
                self.first_run = True
                self.processing_thread = threading.Thread(
                    target=self._processing_loop, daemon=True
                )
                self.processing_thread.start()
            elif not is_start_command:
                debug_logger(
                    message="🔴 STOP command received. Halting marker peak acquisition loop."
                )
                self.stop_event.set()
                if self.processing_thread and self.processing_thread.is_alive():
                    # Give the thread a moment to self-terminate gracefully
                    self.processing_thread.join(timeout=0.5)
                self.processing_thread = None

        except (orjson.JSONDecodeError, ValueError, TypeError) as e:
            debug_logger(message=f"❌ Error processing start/stop command: {e}")

    # Places a batch of up to 6 markers on the instrument.
    # This function publishes the frequencies of the markers in the batch to the appropriate
    # MQTT topics and then triggers the command to place them on the instrument.
    # Inputs:
    #     batch_ids (list): A list of device IDs for the markers to be placed.
    # Outputs:
    #     None.
    def _place_markers_for_batch(self, batch_ids):
        """
        MODULAR FUNCTION: Sets the frequency of up to 6 markers and triggers the
        placement command.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        # --- 1. Place Markers: Publish each marker's frequency (in Hz) ---
        for j, device_id in enumerate(batch_ids, 1):
            marker_topic = f"{TOPIC_MARKER_PLACE_BASE}/marker_{j}_freq_hz/value"
            freq_mhz = self.marker_frequencies.get(device_id, 0)
            freq_hz = int(freq_mhz * HZ_TO_MHZ)

            self.mqtt_util.publish_message(
                topic=marker_topic, subtopic="", value=freq_hz, retain=True
            )

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🐐🔵 Place Marker {j}: {device_id} sent {freq_mhz} MHz ({freq_hz} Hz).",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                )

        time.sleep(0.2)  # Short delay to let the place markers inputs set

        # --- 2. Trigger Place Markers command to set them on device ---
        self.mqtt_util.publish_message(
            TOPIC_MARKER_PLACE_TRIGGER, "", True, retain=False
        )
        self.mqtt_util.publish_message(
            TOPIC_MARKER_PLACE_TRIGGER, "", False, retain=False
        )

        # --- 3. CRITICAL FIX: Add recovery sleep to allow the crash to clear ---
        debug_logger(
            message="🟠 Recovering after Marker Placement to clear potential downstream crash..."
        )
        time.sleep(0.3)  # Allow 4 seconds for the internal exception/crash to resolve

    # Queries the instrument for the peak values of a batch of markers.
    # This function triggers the command to read the marker peak values from the instrument.
    # Inputs:
    #     batch_ids (list): A list of device IDs for the markers being queried.
    # Outputs:
    #     None.
    def _query_markers_for_batch(self, batch_ids):
        """
        NEW FUNCTION: Triggers the NAB query to read the marker peak values.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        # --- 1. Trigger NAB to collect current peaks ---
        debug_logger(message="🔵 Sending NAB query to retrieve current peak markers...")
        self.mqtt_util.publish_message(TOPIC_MARKER_NAB_TRIGGER, "", True, retain=False)
        self.mqtt_util.publish_message(
            TOPIC_MARKER_NAB_TRIGGER, "", False, retain=False
        )

        # --- 2. Flow Control: Wait for NAB query and publishing to complete ---
        debug_logger(message="🟠 Waiting for NAB query and publishing to complete...")
        time.sleep(0.2)  # A minimal, safe wait to ensure messages hit the system.

        debug_logger(
            message=f"✅ Peak retrieval process initiated for batch: {', '.join(batch_ids)}."
        )

    # Sets the instrument's frequency span to encompass all markers.
    # This method calculates the required start and stop frequencies, including a buffer,
    # and sets the instrument accordingly. It only performs the update if the frequency
    # range has changed or on the first run.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _set_instrument_frequency_span(self):
        """
        Sets the instrument to the full frequency span of all markers,
        but only if the min/max frequency has changed or if it's the first run.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if (
            self.min_frequency_mhz == self.last_min_freq
            and self.max_frequency_mhz == self.last_max_freq
            and not self.first_run
        ):

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message="🟢️️️🟡 Min/Max frequencies unchanged. Skipping span update.",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                )
            return

        # Update last known state
        self.last_min_freq = self.min_frequency_mhz
        self.last_max_freq = self.max_frequency_mhz

        # --- APPLY THE BUFFER HERE ---
        # Add buffer to the maximum frequency
        new_max_freq = self.max_frequency_mhz + BUFFER_START_STOP_MHZ
        # Subtract buffer from the minimum frequency (ensuring it doesn't go below zero)
        new_min_freq = max(0, self.min_frequency_mhz - BUFFER_START_STOP_MHZ)

        debug_logger(
            message=f"🔵 Setting instrument span from {new_min_freq} MHz to {new_max_freq} MHz (with {BUFFER_START_STOP_MHZ} MHz buffer)."
        )
        self.mqtt_util.publish_message(
            TOPIC_FREQ_START_INPUT, "", int(new_min_freq * HZ_TO_MHZ), retain=True
        )
        self.mqtt_util.publish_message(
            TOPIC_FREQ_STOP_INPUT, "", int(new_max_freq * HZ_TO_MHZ), retain=True
        )
        self.mqtt_util.publish_message(TOPIC_FREQ_TRIGGER, "", True, retain=False)
        self.mqtt_util.publish_message(TOPIC_FREQ_TRIGGER, "", False, retain=False)
        time.sleep(0.1)  # Short delay to let the frequency rig command process

        self.first_run = False
        debug_logger(message="✅ Instrument span set successfully.")

    # The main processing loop for the worker.
    # This loop continuously sets the instrument's frequency span and then iterates through
    # all markers in batches, placing them on the instrument and querying their peak values.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _processing_loop(self):
        """
        The main logic loop that runs in a thread.
        """
        debug_logger(message="✅ Peak Hunter loop started.")

        # --- Loop Control: Check the stop event first ---
        while not self.stop_event.is_set():
            # NOTE: Removed redundant check on TOPIC_START_STOP as stop_event handles thread control.

            # --- Step 1: Set the instrument to the full frequency span of all markers (Conditional) ---
            self._set_instrument_frequency_span()

            # --- Step 2: Loop through markers in batches of 6 ---
            device_ids = sorted(self.marker_frequencies.keys())

            for i in range(0, len(device_ids), 6):
                if self.stop_event.is_set():
                    debug_logger(
                        message="Loop terminated by STOP command during batch processing."
                    )
                    break

                batch_ids = device_ids[i : i + 6]

                # Use the dedicated modular function to handle marker placement
                self._place_markers_for_batch(batch_ids=batch_ids)

                # --- DELAY as requested ---
                time.sleep(0.5)

                # Use the dedicated modular function to query the batch
                self._query_markers_for_batch(batch_ids=batch_ids)

                # --- Confirmation log and flow control ---
                debug_logger(
                    message=f"✅ Batch {i//6 + 1} processed. Continuing to next batch."
                )

            debug_logger(message="✅ Peak Hunter loop finished a full pass.")


# --- TUNING HELPER FUNCTIONS (Moved from worker_marker_tune_to_marker.py) ---


# Tunes the instrument to a marker's center frequency.
# This function publishes MQTT messages to set the instrument's center frequency and span
# based on a selected marker's data, then triggers the command to apply the settings.
# Inputs:
#     mqtt_controller (MqttControllerUtility): The MQTT utility for publishing messages.
#     marker_data (dict): A dictionary containing the marker's data, including 'FREQ_MHZ'.
# Outputs:
#     None.
def Push_Marker_to_Center_Freq(mqtt_controller, marker_data):
    """
    Publishes MQTT messages to set the instrument's center frequency and span
    based on a selected marker, and then triggers the SCPI command.
    """
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message="🟢️️️🟢 Received request to tune to marker. Processing data...",
            file=current_file,
            version=current_version,
            function=f"{current_function}",
        )

    try:
        # Define the MQTT topics as constants
        CENTER_FREQ_TOPIC = (
            "OPEN-AIR/yak/Frequency/beg/Beg_freq_center_span/Input/center_freq/value"
        )
        SPAN_FREQ_TOPIC = (
            "OPEN-AIR/yak/Frequency/beg/Beg_freq_center_span/Input/span_freq/value"
        )
        TRIGGER_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_center_span/scpi_details/Execute Command/trigger"

        DEFAULT_SPAN_HZ = 1000000  # 1 MHz

        freq_mhz = marker_data.get("FREQ_MHZ", None)
        if freq_mhz is None:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message="❌🔴 Error: Marker data is missing the 'FREQ_MHZ' key.",
                    file=current_file,
                    version=current_version,
                    function=f"{current_function}",
                )
            debug_logger(message="❌ Failed to tune: Marker data is incomplete.")
            return

        try:
            freq_mhz = float(freq_mhz)
            # FIX: Convert to integer for HZ value
            center_freq_hz = int(freq_mhz * HZ_TO_MHZ)
        except (ValueError, TypeError) as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌🔴 Error converting frequency to float: {e}",
                    file=current_file,
                    version=current_version,
                    function=f"{current_function}",
                )
            debug_logger(message="❌ Failed to tune: Invalid frequency value.")
            return

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Freq from marker: {freq_mhz} MHz -> {center_freq_hz} Hz. Setting Span to {DEFAULT_SPAN_HZ} Hz.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )

        # FIX: Ensure all values published are integers
        mqtt_controller.publish_message(
            topic=CENTER_FREQ_TOPIC, subtopic="", value=center_freq_hz
        )
        debug_logger(message=f"✅ Set CENTER_FREQ to {center_freq_hz} Hz.")

        mqtt_controller.publish_message(
            topic=SPAN_FREQ_TOPIC, subtopic="", value=int(DEFAULT_SPAN_HZ)
        )
        debug_logger(message=f"✅ Set SPAN_FREQ to {int(DEFAULT_SPAN_HZ)} Hz.")

        mqtt_controller.publish_message(topic=TRIGGER_TOPIC, subtopic="", value=True)
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🔵 Trigger set to True. Awaiting instrument response.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )

        mqtt_controller.publish_message(topic=TRIGGER_TOPIC, subtopic="", value=False)
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🔵 Trigger reset to False. Command sequence complete.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )

        debug_logger(message="✅ Tuning command sequence complete.")

    except Exception as e:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌🔴 Critical error during marker tuning: {e}",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )
        debug_logger(message=f"❌ An error occurred while tuning to the marker: {e}")


# Tunes the instrument to a frequency range centered around a marker.
# This function calculates start and stop frequencies based on a marker's frequency and a
# specified buffer, then publishes these values and triggers the command to apply them.
# Inputs:
#     mqtt_controller (MqttControllerUtility): The MQTT utility for publishing messages.
#     marker_data (dict): A dictionary containing the marker's data, including 'FREQ_MHZ'.
#     buffer (float, optional): The frequency buffer in Hz to apply around the center frequency.
# Outputs:
#     None.
def Push_Marker_to_Start_Stop_Freq(mqtt_controller, marker_data, buffer=1e6):
    """
    Calculates start and stop frequencies based on a marker frequency and a buffer,
    then publishes the values and triggers the SCPI command.
    """
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"🟢️️️🟢 Received request to tune with a buffer. Buffer is {buffer} Hz. Processing data...",
            file=current_file,
            version=current_version,
            function=f"{current_function}",
        )

    try:
        # Define the MQTT topics as constants
        START_FREQ_TOPIC = (
            "OPEN-AIR/yak/Frequency/beg/Beg_freq_start_stop/Input/start_freq/value"
        )
        STOP_FREQ_TOPIC = (
            "OPEN-AIR/yak/Frequency/beg/Beg_freq_start_stop/Input/stop_freq/value"
        )
        START_STOP_TRIGGER_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_start_stop/scpi_details/Execute Command/trigger"

        freq_mhz = marker_data.get("FREQ_MHZ", None)
        if freq_mhz is None:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message="❌🔴 Error: Marker data is missing the 'FREQ_MHZ' key.",
                    file=current_file,
                    version=current_version,
                    function=f"{current_function}",
                )
            debug_logger(message="❌ Failed to tune: Marker data is incomplete.")
            return

        try:
            freq_mhz = float(freq_mhz)
            center_freq_hz = freq_mhz * HZ_TO_MHZ
        except (ValueError, TypeError) as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌🔴 Error converting frequency to float: {e}",
                    file=current_file,
                    version=current_version,
                    function=f"{current_function}",
                )
            debug_logger(message="❌ Failed to tune: Invalid frequency value.")
            return

        # Calculate start and stop frequencies
        # FIX: Convert to integer for HZ value
        start_freq_hz = int(center_freq_hz - buffer)
        stop_freq_hz = int(center_freq_hz + buffer)

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Calculated range: Start={start_freq_hz} Hz, Stop={stop_freq_hz} Hz.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )

        # Publish start frequency
        mqtt_controller.publish_message(
            topic=START_FREQ_TOPIC, subtopic="", value=start_freq_hz
        )
        debug_logger(message=f"✅ Set START_FREQ to {start_freq_hz} Hz.")

        # Publish stop frequency
        mqtt_controller.publish_message(
            topic=STOP_FREQ_TOPIC, subtopic="", value=stop_freq_hz
        )
        debug_logger(message=f"✅ Set STOP_FREQ to {stop_freq_hz} Hz.")

        # Trigger SCPI command
        mqtt_controller.publish_message(
            topic=START_STOP_TRIGGER_TOPIC, subtopic="", value=True
        )
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🔵 Trigger set to True. Awaiting instrument response.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )

        # Reset the trigger
        mqtt_controller.publish_message(
            topic=START_STOP_TRIGGER_TOPIC, subtopic="", value=False
        )
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🔵 Trigger reset to False. Command sequence complete.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )

        debug_logger(message="✅ Tuning command sequence complete.")

    except Exception as e:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌🔴 Critical error during marker tuning with buffer: {e}",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
            )
        debug_logger(
            message=f"❌ An error occurred while tuning to the marker with a buffer: {e}"
        )