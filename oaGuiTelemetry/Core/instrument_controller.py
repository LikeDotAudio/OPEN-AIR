# Core/instrument_controller.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
HZ_TO_MHZ = 1_000_000

# YAK Frequency Topics
TOPIC_FREQ_START_INPUT = "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/Input/start_freq/value"
TOPIC_FREQ_STOP_INPUT = "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/Input/stop_freq/value"
TOPIC_FREQ_TRIGGER = "OPEN-AIR/yak/Frequency/rig/Rig_freq_start_stop/scpi_details/Execute Command/trigger"

# YAK Marker Placement Topics
TOPIC_MARKER_PLACE_BASE = "OPEN-AIR/yak/Markers/beg/Beg_Place_All_markers/Input"
TOPIC_MARKER_PLACE_TRIGGER = "OPEN-AIR/yak/Markers/beg/Beg_Place_All_markers/scpi_details/Execute Command/trigger"

# YAK Marker Value Retrieval (NAB) Topics
TOPIC_MARKER_NAB_TRIGGER = "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/scpi_details/Execute Command/trigger"

class InstrumentController:
    """
    Handles SCPI-over-MQTT commands for the instrument (Frequency Span, Marker Placement, NAB Query).
    """

    def __init__(self, mqtt_util):
        self.mqtt_util = mqtt_util

    def set_span(self, min_freq_mhz, max_freq_mhz):
        """Sets the instrument start/stop frequencies in Hz."""
        if LOCAL_DEBUG: logger.debug(f"🔵 Setting instrument span from {min_freq_mhz} MHz to {max_freq_mhz} MHz.")
        self.mqtt_util.publish_message(TOPIC_FREQ_START_INPUT, "", int(min_freq_mhz * HZ_TO_MHZ), retain=True)
        self.mqtt_util.publish_message(TOPIC_FREQ_STOP_INPUT, "", int(max_freq_mhz * HZ_TO_MHZ), retain=True)
        self.mqtt_util.publish_message(TOPIC_FREQ_TRIGGER, "", True, retain=False)
        self.mqtt_util.publish_message(TOPIC_FREQ_TRIGGER, "", False, retain=False)
        if LOCAL_DEBUG: logger.success("✅ Instrument span set successfully.")

    def place_markers_batch(self, batch_frequencies_mhz):
        """
        Sets frequencies of up to 6 markers on the instrument and triggers placement.
        """
        for j, freq_mhz in enumerate(batch_frequencies_mhz, 1):
            marker_topic = f"{TOPIC_MARKER_PLACE_BASE}/marker_{j}_freq_hz/value"
            freq_hz = int(freq_mhz * HZ_TO_MHZ)
            self.mqtt_util.publish_message(topic=marker_topic, subtopic="", value=freq_hz, retain=True)
            if LOCAL_DEBUG: logger.debug(f"🐐🔵 Place Marker {j}: {freq_mhz} MHz -> {freq_hz} Hz.")

        # Trigger placement
        self.mqtt_util.publish_message(TOPIC_MARKER_PLACE_TRIGGER, "", True, retain=False)
        self.mqtt_util.publish_message(TOPIC_MARKER_PLACE_TRIGGER, "", False, retain=False)
        if LOCAL_DEBUG: logger.debug("🟠 Marker placement command triggered.")

    def trigger_nab_query(self):
        """Triggers NAB to collect marker peak data."""
        if LOCAL_DEBUG: logger.debug("🔵 Sending NAB query to retrieve current peaks...")
        self.mqtt_util.publish_message(TOPIC_MARKER_NAB_TRIGGER, "", True, retain=False)
        self.mqtt_util.publish_message(TOPIC_MARKER_NAB_TRIGGER, "", False, retain=False)
        if LOCAL_DEBUG: logger.success("✅ NAB peak retrieval initiated.")
