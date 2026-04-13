# oaComProtocols.oaComMidi/Workers/midi_mqtt_worker.py
#
# Standalone MQTT Worker for the MIDI Module.
# Enables direct MQTT publishing and subscribing without ProtocolRouter.
#
# Author: Gemini CLI
# Version: 20260411.1530.1

import threading
import paho.mqtt.client as mqtt
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
import orjson

class MidiMqttWorker:
    """
    Handles direct MQTT communication for the MIDI module when in standalone mode.
    """
    def __init__(self, midi_manager):
        self.midi_manager = midi_manager
        self.config = Config.get_instance()
        self.client = None
        self._running = False
        self._thread = None
        
        # Connection Settings from config.ini
        self.broker = self.config.MQTT_BROKER_ADDRESS
        self.port = self.config.MQTT_BROKER_PORT
        self.username = self.config.MQTT_USERNAME
        self.password = self.config.MQTT_PASSWORD
        self.retain = self.config.MQTT_RETAIN_BEHAVIOR
        
        # Base topic for MIDI
        self.base_topic = "OPEN-AIR/MIDI/#"

    def start(self):
        if self._running: return
        self._running = True
        
        self.client = mqtt.Client(client_id=f"oaMidiStandalone_{threading.get_ident()}")
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
            
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        matrix_log("comms", "midi", "start", f"📡 [MIDI-MQTT] Connecting to {self.broker}:{self.port}...", "INFO")
        
        try:
            self.client.connect(self.broker, self.port, 60)
            self._thread = threading.Thread(target=self.client.loop_forever, daemon=True)
            self._thread.start()
        except Exception as e:
            logger.error(f"📡 [MIDI-MQTT] Connection Failed: {e}")
            self._running = False

    def stop(self):
        self._running = False
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            matrix_log("comms", "midi", "_on_connect", "📡 [MIDI-MQTT] Connected to broker.", "SUCCESS")
            client.subscribe(self.base_topic)
            matrix_log("comms", "midi", "_on_connect", f"📡 [MIDI-MQTT] Subscribed to {self.base_topic}", "INFO")
        else:
            logger.error(f"📡 [MIDI-MQTT] Connection failed with code {rc}")

    def _on_message(self, client, userdata, message):
        try:
            if not message.payload:
                return

            topic = message.topic
            payload = orjson.loads(message.payload)
            
            # ⚡ ECHO PREVENTION: Identify if this message was authored by the local instance.
            meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
            message_src_id = meta.get("src") or meta.get("full_id")
            if message_src_id == self.config.FULL_INSTANCE_ID:
                return

            matrix_log("comms", "midi", "_on_message", f"📡 [MIDI-MQTT] Message RX: {topic}", "TRACE")
            
            # Forward to MidiManager to handle as an external event
            # Use 'MIDI-MQTT' to bypass the 'MQTT' echo prevention check in MidiManager
            event_message = {
                "topic": topic,
                "value": payload.get("value") if isinstance(payload, dict) else payload,
                "meta": meta,
                "source": "MIDI-MQTT",
                "logical_source": meta.get("origin_source", "MQTT") 
            }
            self.midi_manager._on_protocol_event(event_message)
            
        except Exception as e:
            logger.error(f"📡 [MIDI-MQTT] Error processing MQTT message: {e}")

    def publish(self, topic, payload, meta=None):
        if not self.client or not self._running: return
        
        try:
            # Standardized payload structure
            m = meta or {}
            # ⚡ ESSENTIAL: Inject local identity for echo prevention
            m["src"] = self.config.FULL_INSTANCE_ID
            m["full_id"] = self.config.FULL_INSTANCE_ID
            
            full_payload = {
                "value": payload,
                "meta": m
            }
            
            encoded_payload = orjson.dumps(full_payload)
            self.client.publish(topic, encoded_payload, retain=self.retain)
            matrix_log("comms", "midi", "publish", f"📡 [MIDI-MQTT] Published to {topic}", "TRACE")
        except Exception as e:
            logger.error(f"📡 [MIDI-MQTT] Publish failed: {e}")
