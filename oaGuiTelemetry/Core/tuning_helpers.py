from oaLogging.Methods.matrix_gate import matrix_log
# Core/tuning_helpers.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger
import inspect

# --- Standard Debug Logging Setup ---
HZ_TO_MHZ = 1_000_000

# Topics for Center/Span Tuning
CENTER_FREQ_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_center_span/Input/center_freq/value"
SPAN_FREQ_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_center_span/Input/span_freq/value"
TRIGGER_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_center_span/scpi_details/Execute Command/trigger"

# Topics for Start/Stop Tuning
START_FREQ_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_start_stop/Input/start_freq/value"
STOP_FREQ_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_start_stop/Input/stop_freq/value"
START_STOP_TRIGGER_TOPIC = "OPEN-AIR/yak/Frequency/beg/Beg_freq_start_stop/scpi_details/Execute Command/trigger"

def Push_Marker_to_Center_Freq(mqtt_controller, marker_data):
    """Tunes the instrument to a marker's center frequency with a default 1 MHz span."""
    try:
        freq_mhz = marker_data.get("FREQ_MHZ")
        if freq_mhz is None:
            logger.error("❌ Failed to tune: Marker data is missing 'FREQ_MHZ'.")
            return

        center_freq_hz = int(float(freq_mhz) * HZ_TO_MHZ)
        default_span_hz = 1_000_000

        mqtt_controller.publish_message(topic=CENTER_FREQ_TOPIC, subtopic="", value=center_freq_hz)
        mqtt_controller.publish_message(topic=SPAN_FREQ_TOPIC, subtopic="", value=default_span_hz)
        
        mqtt_controller.publish_message(topic=TRIGGER_TOPIC, subtopic="", value=True)
        mqtt_controller.publish_message(topic=TRIGGER_TOPIC, subtopic="", value=False)
        
        matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Tuned to {freq_mhz} MHz (Span: 1 MHz).", "SUCCESS")
    except Exception as e:
        logger.exception(f"❌ Error during marker center tuning: {e}")

def Push_Marker_to_Start_Stop_Freq(mqtt_controller, marker_data, buffer=1_000_000):
    """Tunes the instrument to a frequency range around a marker with a specified buffer."""
    try:
        freq_mhz = marker_data.get("FREQ_MHZ")
        if freq_mhz is None:
            logger.error("❌ Failed to tune: Marker data is missing 'FREQ_MHZ'.")
            return

        center_freq_hz = float(freq_mhz) * HZ_TO_MHZ
        start_freq_hz = int(center_freq_hz - buffer)
        stop_freq_hz = int(center_freq_hz + buffer)

        mqtt_controller.publish_message(topic=START_FREQ_TOPIC, subtopic="", value=start_freq_hz)
        mqtt_controller.publish_message(topic=STOP_FREQ_TOPIC, subtopic="", value=stop_freq_hz)
        
        mqtt_controller.publish_message(topic=START_STOP_TRIGGER_TOPIC, subtopic="", value=True)
        mqtt_controller.publish_message(topic=START_STOP_TRIGGER_TOPIC, subtopic="", value=False)
        
        matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Tuned to range {start_freq_hz} - {stop_freq_hz} Hz.", "SUCCESS")
    except Exception as e:
        logger.exception(f"❌ Error during marker start/stop tuning: {e}")
