
import datetime
import inspect

# Methods/active_peak_publisher.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Event-driven worker that transforms flat marker data into a hierarchical
import orjson
from loguru import logger

from oaComProtocols.oaComMQTT.Methods.mqtt_controller_util import MqttControllerUtility
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

LOCAL_DEBUG = False

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20251006.223430.3"
TOPIC_MARKER_PEAK_WILDCARD = "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/Outputs/+/value"
TOPIC_MARKER_FREQ_WILDCARD = "OPEN-AIR/yak/Markers/nab/NAB_all_marker_settings/Outputs/+/value"
TOPIC_MEASUREMENTS_ROOT = "OPEN-AIR/measurements"
TOPIC_DELIMITER = "/"

class ActivePeakPublisher:
    """
    Transforms flat marker data into a hierarchical frequency-based topic structure.
    """

    def __init__(self, mqtt_util: MqttControllerUtility):
        if LOCAL_DEBUG:
            matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟢 Initializing ActivePeakPublisher.", "DEBUG")
        self.mqtt_util = mqtt_util
        self.marker_data_buffer = {}
        self._setup_subscriptions()
        if LOCAL_DEBUG:
            matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ ActivePeakPublisher online.", "SUCCESS")

    def _setup_subscriptions(self):
        self.mqtt_util.add_subscriber(TOPIC_MARKER_PEAK_WILDCARD, self._on_marker_message)
        self.mqtt_util.add_subscriber(TOPIC_MARKER_FREQ_WILDCARD, self._on_marker_message)

    def _parse_marker_payload(self, payload):
        """Extracts numeric value from JSON payload safely."""
        try:
            payload_dict = orjson.loads(payload)
            value_str = payload_dict.get("value")
            return float(value_str)
        except (orjson.JSONDecodeError, ValueError, TypeError):
            return None

    def _on_marker_message(self, topic, payload):
        """Primary callback for incoming marker data."""
        numeric_value = self._parse_marker_payload(payload)
        if numeric_value is None:
            if LOCAL_DEBUG:
                matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"⚠️ Unparsable payload: {payload}", "DEBUG")
            return

        is_frequency = "freq" in topic
        marker_id = topic.split(TOPIC_DELIMITER)[-2].replace("_freq", "")

        if marker_id not in self.marker_data_buffer:
            self.marker_data_buffer[marker_id] = {"peak": None, "freq_hz": None}

        if is_frequency:
            self.marker_data_buffer[marker_id]["freq_hz"] = numeric_value
        else:
            self.marker_data_buffer[marker_id]["peak"] = numeric_value

        self._check_marker_pair_completeness(marker_id)

    def _check_marker_pair_completeness(self, marker_id):
        """Checks if both peak and frequency are available for a marker."""
        entry = self.marker_data_buffer[marker_id]
        if entry["peak"] is not None and entry["freq_hz"] is not None:
            self._republish_to_hierarchical_topic(
                marker_id=marker_id,
                freq_hz=entry["freq_hz"],
                peak_dbm=entry["peak"]
            )
            del self.marker_data_buffer[marker_id]

    def _republish_to_hierarchical_topic(self, marker_id, freq_hz, peak_dbm):
        """Constructs and publishes to hierarchical frequency topics."""
        try:
            freq_mhz = freq_hz / 1_000_000.0

            # Breakdown for path: GHz/100M/10M/1M/100k/10k/1k
            ghz = int(freq_mhz // 1000)
            m_rem = freq_mhz % 1000
            m100 = int(m_rem // 100)
            m_rem %= 100
            m10 = int(m_rem // 10)
            m1 = int(m_rem % 10)

            k_total = round((freq_mhz - int(freq_mhz)) * 1000.0, 0)
            k100 = int(k_total // 100)
            k_rem = k_total % 100
            k10 = int(k_rem // 10)
            k1 = int(k_rem % 10)

            topic_path = TOPIC_DELIMITER.join(map(str, [ghz, m100, m10, m1, k100, k10, k1]))
            full_topic = f"{TOPIC_MEASUREMENTS_ROOT}/{topic_path}"

            final_payload = {
                "Marker": marker_id,
                "Peak_dBm": round(peak_dbm, 2),
                "Source_Freq_MHz": round(freq_mhz, 6),
                "Timestamp": datetime.datetime.now().isoformat(),
            }

            self.mqtt_util.publish_message(
                topic=full_topic,
                subtopic="",
                value=orjson.dumps(final_payload).decode(),
                retain=True,
            )

            if LOCAL_DEBUG:
                matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Reposted {marker_id} ({round(freq_mhz, 3)} MHz) to {full_topic}", "SUCCESS")

        except Exception:
            if LOCAL_DEBUG:
                logger.exception(f"❌ Error republishing marker {marker_id}")
