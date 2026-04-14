# oaComProtocols.oaComMidi/Workers/midi_mqtt_worker.py
#
# Standalone MQTT Worker wrapper for the MIDI Module.
# ⚡ REFACTORED: Now wraps the Native Core MidiMqttTransport.
#
# Author: Gemini CLI (Collaborator)
# Version: 20260414.1810.1

from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from ..Core.midi_mqtt_transport import MidiMqttTransport

class MidiMqttWorker:
    """
    Handles direct MQTT communication for the MIDI module when in standalone mode.
    Acts as a worker wrapper around the Core MidiMqttTransport.
    """
    def __init__(self, midi_manager, transport=None):
        self.midi_manager = midi_manager
        self.config = Config.get_instance()
        self.transport = transport or MidiMqttTransport()
        self._running = False
        
        # Base topic for MIDI
        self.base_topic = "OPEN-AIR/MIDI/#"

    def start(self):
        if self._running: return
        
        # Setup message handler before connecting
        self.transport.set_message_handler(self._on_transport_message)
        
        connection_params = {
            "destination_host": self.config.MQTT_BROKER_ADDRESS,
            "destination_port": self.config.MQTT_BROKER_PORT,
            "username": self.config.MQTT_USERNAME,
            "password": self.config.MQTT_PASSWORD,
            "client_id": f"oaMidiWorker_{self.config.FULL_INSTANCE_ID[:8]}"
        }
        
        if self.transport.connect(connection_params):
            self._running = True
            self.transport.subscribe(self.base_topic)
            matrix_log("comms", "midi", "start", "📡 [MIDI-WORKER] Worker started with Core Transport.", "SUCCESS")
        else:
            logger.error("📡 [MIDI-WORKER] Failed to start Core Transport.")

    def stop(self):
        self._running = False
        if self.transport:
            self.transport.disconnect()

    def _on_transport_message(self, topic, payload):
        """Unified callback from Core Transport."""
        try:
            # ⚡ EFFICIENT ROUTING: Forward to MidiManager
            # The core transport already handled JSON decoding and echo prevention (src check)
            
            meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
            
            event_message = {
                "topic": topic,
                "value": payload.get("value") if isinstance(payload, dict) else payload,
                "meta": meta,
                "source": "MIDI-MQTT",
                "logical_source": meta.get("origin_source", "MQTT") 
            }
            self.midi_manager._on_protocol_event(event_message)
            
        except Exception as e:
            logger.error(f"📡 [MIDI-WORKER] Error processing transport message: {e}")

    def publish(self, topic, payload, meta=None):
        """Legacy publish shim that delegates to core transport."""
        if not self.transport: return
        
        # Standardized payload structure
        m = meta or {}
        # Core transport handles src injection if we pass a dict correctly
        full_payload = {
            "value": payload,
            "meta": m
        }
        self.transport.publish(topic, full_payload, retain=self.config.MQTT_RETAIN_BEHAVIOR)
