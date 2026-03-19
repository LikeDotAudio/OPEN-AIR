from ..Constants.constants import splinker_logger

def handle_mqtt_command(self, topic, payload):
    splinker_logger.info(f"📥 Splinker: handle_mqtt_command(topic={topic})")
    self._handle_command(topic, payload)
