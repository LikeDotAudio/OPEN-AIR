import orjson
from loguru import logger

class MarkerRepositoryWatcher:
    """
    Watches the Marker Repository on MQTT and maintains a local state of frequencies and stats.
    """

    def __init__(self):
        self.total_devices = 0
        self.min_frequency_mhz = 0.0
        self.max_frequency_mhz = 0.0
        self.marker_frequencies = {}

    def on_marker_update(self, topic, payload):
        """
        Parses MQTT messages and updates internal frequency/stat state.
        """
        try:
            try:
                value = orjson.loads(payload).get("value")
            except (orjson.JSONDecodeError, AttributeError):
                value = payload

            if topic.endswith("/total_devices"):
                self.total_devices = int(value)
            elif topic.endswith("/min_frequency_mhz"):
                self.min_frequency_mhz = float(value)
            elif topic.endswith("/max_frequency_mhz"):
                self.max_frequency_mhz = float(value)
            elif topic.endswith("/IDENTITY/FREQ_MHZ"):
                topic_parts = topic.split("/")
                if len(topic_parts) >= 4 and topic_parts[-3].startswith("Device-"):
                    device_id = topic_parts[-3]
                    self.marker_frequencies[device_id] = float(value)
                    return device_id
        except Exception as e:
            logger.debug(f"🟡 Warning: Could not process marker data update: {e}")
        return None
