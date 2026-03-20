# oaComMQTT/Constants/mqtt_config.py
# Standard MQTT configuration defaults and state constants.

DEFAULT_MQTT_KEEPALIVE = 60
DEFAULT_MQTT_TIMEOUT = 10
DEFAULT_QOS = 0
RECONNECT_DELAY = 5.0

# System Topics
TOPIC_STATUS = "OPEN-AIR/status"
PAYLOAD_OFFLINE = "OFFLINE"
PAYLOAD_ONLINE = "ONLINE"

# Worker Settings
WORKER_KICK_TIMEOUT = 5.0
MAX_PUBLISH_BATCH = 100
