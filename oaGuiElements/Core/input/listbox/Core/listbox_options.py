import orjson
from loguru import logger
from oaComMQTT.Methods.mqtt_topic_utils import TOPIC_DELIMITER

class ListboxOptionsManager:
    """Manages the internal model of listbox options and processes remote MQTT updates."""

    def __init__(self, initial_options):
        self.options_map = initial_options if isinstance(initial_options, dict) else {str(i): v for i, v in enumerate(initial_options)}

    def process_mqtt_update(self, topic, payload, expected_prefix):
        """Updates the options map based on hierarchical MQTT property paths."""
        try:
            data = orjson.loads(payload); value = data.get("val")
            rel_path = topic[len(expected_prefix):].strip(TOPIC_DELIMITER)
            parts = rel_path.split(TOPIC_DELIMITER)
            if len(parts) < 2: return None

            opt_key, prop = parts[0], parts[1]
            if opt_key not in self.options_map: self.options_map[opt_key] = {"active": "true"}
            
            if prop in ["active", "selected"]: self.options_map[opt_key][prop] = str(value).lower()
            else: self.options_map[opt_key][prop] = value
            
            return opt_key if (prop == "selected" and value is True) else True
        except Exception as e:
            logger.error(f"❌ Listbox options update failed: {e}"); return None

    def get_sorted_active(self):
        """Returns a list of (key, config) for all currently active options."""
        active = {k: v for k, v in self.options_map.items() if str(v.get("active", "true")).lower() in ["true", "yes"]}
        return sorted(active.items(), key=lambda x: str(x[1].get("value", x[0])))
