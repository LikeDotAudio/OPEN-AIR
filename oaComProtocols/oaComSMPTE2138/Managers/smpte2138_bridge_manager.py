# oaComProtocols.oaComSMPTE2138/Managers/smpte2138_bridge_manager.py
#
# Manages the bridge between the internal OPEN-AIR MQTT actions and the 
# external SMPTE2138 (ST 2138) Protobuf-encoded namespace.
# Supports remote start/stop control via MQTT and direct ProtocolRouter events.
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
# Version 20260330.1600.1

import os
import sys
import time
import orjson
from pathlib import Path
from loguru import logger

# --- Path Guard for Protobuf Imports ---
interface_path = Path(__file__).resolve().parents[1] / "Interface"
if str(interface_path) not in sys.path:
    sys.path.insert(0, str(interface_path))

# --- Protobuf Imports ---
from oaComProtocols.oaComSMPTE2138.Interface import param_pb2
from oaComProtocols.oaComSMPTE2138.Interface import device_pb2

# --- Standard OPEN-AIR Imports ---
from oaLogging.Core.logger import SMPTE2138_LOGGER
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter

def _is_debug():
    from oaLogging.Methods.matrix_gate import is_debug_allowed
    return is_debug_allowed(system="comms", element="smpte2138")

class SMPTE2138BridgeManager:
    """
    Translates internal MQTT actions into SMPTE2138 binary Protobuf payloads.
    Includes lifecycle control for enabling/disabling the translation engine.
    """

    def __init__(self, mqtt_connection: MqttConnectionManager, 
                 subscriber_router: MqttSubscriberRouter):
        self.mqtt = mqtt_connection
        self.router = subscriber_router
        self.slot = 1
        
        # State Control
        self.bridge_enabled = True # Enabled by default
        
        # Internal OID mapping
        # Maps both raw MQTT topics and Router-normalized paths
        self.topic_to_oid = {
            "oa/action/sig_gen/frequency": "frequency",
            "oa/action/sig_gen/amplitude": "amplitude",
            "oa/action/sig_gen/waveform": "waveform",
            "oa/action/device/play": "play",
            # Normalized paths from GUI interactions
            "OPEN-AIR/Assets/Spectrum/Instrument/frequency/Spectrum_Instrument_frequency/blocks/Frequency/span_freq_MHz": "frequency",
            "OPEN-AIR/Assets/Spectrum/Instrument/frequency/Spectrum_Instrument_frequency/blocks/Start Stop/start_freq_MHz": "frequency_start",
            "OPEN-AIR/Assets/Spectrum/Instrument/frequency/Spectrum_Instrument_frequency/blocks/Frequency/center_freq_MHz": "frequency_center"
        }
        
        self._setup_subscriptions()
        self._publish_bridge_status()
        
        matrix_log("comms", "smpte2138", "__init__", "✅ [BRIDGE] SMPTE2138 Protocol Bridge initialized and active.", "SUCCESS")

    def start(self):
        """Standardized entry point for the ProtocolRouter to activate the bridge."""
        if not self.bridge_enabled:
            self.bridge_enabled = True
            matrix_log("comms", "smpte2138", "start", "▶️ [BRIDGE] SMPTE2138 Protocol Bridge started (PRIMARY).", "INFO")
            self._publish_bridge_status()

    def stop(self):
        """Standardized entry point for the ProtocolRouter to deactivate the bridge."""
        if self.bridge_enabled:
            self.bridge_enabled = False
            matrix_log("comms", "smpte2138", "stop", "⏹️ [BRIDGE] SMPTE2138 Protocol Bridge stopped (SHADOW).", "INFO")
            self._publish_bridge_status()

    def _setup_subscriptions(self):
        """Registers listeners for internal actions and remote control."""
        # 1. Action Triggers (Raw MQTT fallback)
        # self.router.subscribe_to_topic("oa/action/#", self._on_internal_action)
        
        # 2. Remote Bridge Control (from GUI)
        self.router.subscribe_to_topic("OPEN-AIR/System/Control/SMPTE2138/Bridge", self._on_remote_control)
        
        matrix_log("comms", "smpte2138", "_setup_subscriptions", "👂 [LISTEN] Bridge active and listening for control (Actions & Status).", "DEBUG")


    def handle_router_event(self, topic, val, meta=None):
        """
        Direct entry point from ProtocolRouter dispatch.
        Bypasses raw MQTT subscription for higher reliability.
        """
        if not self.bridge_enabled: return
        
        # ⚡ V3.1.13 NAMESPACE EXCLUSION:
        # System and Monitor topics should never be mirrored to the ST2138 bus.
        if "/System/" in topic or "/Monitor/" in topic:
            return

        meta = meta or {}
        # The Asynchronous "Listen-and-Filter" Loop
        # Filter out traffic generated by SMPTE2138 itself
        if meta.get("origin_source") == "SMPTE2138":
            return
            
        # ⚡ ENHANCEMENT: Handle enriched payloads (e.g., from MIDI or REST)
        # If val is a dict, extract the primary numeric or boolean value.
        real_val = val
        if isinstance(val, dict) and "val" in val:
            real_val = val["val"]
            # Merge dictionary into metadata if it's not already there
            meta = meta or {}
            for k, v in val.items():
                if k != "val": meta[k] = v

        meta = meta or {}
        bin_id = meta.get("bin_id")
        block_name = meta.get("block_name")
        field_name = meta.get("field_name")

        # 1. Resolve Slot (Default to self.slot if not in meta)
        slot = self.slot
        if bin_id:
            slot = self._derive_slot(bin_id)

        # 2. Resolve OID
        oid = self.topic_to_oid.get(topic)
        
        # ⚡ ARCHITECT'S CHOICE: Mirror the builder hierarchy if structural metadata is present
        if block_name and field_name:
            oid = f"{block_name}/{field_name}"
        
        # ⚡ GENERIC FALLBACK: If no OID is mapped, use a portion of the topic path.
        if not oid:
            # We strip the root namespace to create a relative OID
            oid = topic.replace("OPEN-AIR/", "")
        
        if not oid: 
            # Silent skip for unmapped or empty topics
            return
        
        try:
            if isinstance(real_val, (int, float, bool)):
                # Convert bool to float for ST2138 standard
                f_val = float(real_val) if not isinstance(real_val, bool) else (1.0 if real_val else 0.0)
                self._publish_parameter(oid, f_val, slot_override=slot)
            else:
                self._publish_command(oid, str(real_val), slot_override=slot)
        except Exception as e:
            SMPTE2138_LOGGER.error(f"❌ [BRIDGE] Router Event Translation failure: {e}")



    def _derive_slot(self, bin_id: str) -> int:
        """
        Converts a dot-separated Bin ID (e.g. '50.100.5.1.1') into a uint32 slot.
        Strips dots and converts to integer. Handles up to ~4 billion.
        """
        try:
            # Flatten 50.100.0.3.1 -> 50100031
            numeric_str = str(bin_id).replace(".", "")
            slot = int(numeric_str)
            # Clamp to uint32 max
            return slot & 0xFFFFFFFF
        except (ValueError, TypeError):
            return self.slot

    def _publish_parameter(self, oid: str, value: float, slot_override=None):
        slot = slot_override or self.slot
        payload = param_pb2.SingleSetValuePayload()
        payload.slot = slot
        payload.value.oid = oid
        payload.value.value.float32_value = value
        
        binary_payload = payload.SerializeToString()
        smpte2138_topic = f"st2138/device/{slot}/param/{oid}"
        
        self.mqtt.publish(
            topic=smpte2138_topic,
            payload=binary_payload,
            qos=0,
            retain=False
        )
        matrix_log("comms", "smpte2138", "_publish_parameter", f"📡📤📤 [SMPTE2138] Published FLOAT32 to {smpte2138_topic} ({value})", "INFO")

    def _publish_command(self, oid: str, value: str, slot_override=None):
        slot = slot_override or self.slot
        payload = param_pb2.ExecuteCommandPayload()
        payload.slot = slot
        payload.oid = oid
        payload.value.string_value = value
        payload.respond = True
        
        binary_payload = payload.SerializeToString()
        smpte2138_topic = f"st2138/device/{slot}/cmd/{oid}"
        
        self.mqtt.publish(
            topic=smpte2138_topic,
            payload=binary_payload,
            qos=0,
            retain=False
        )
        matrix_log("comms", "smpte2138", "_publish_command", f"🚀📤📤 [SMPTE2138] Published COMMAND to {smpte2138_topic} ({value})", "INFO")

    def _on_remote_control(self, msg):
        """Processes remote start/stop commands."""
        try:
            payload = msg.payload
            data = orjson.loads(payload) if isinstance(payload, (bytes, str)) else payload
            
            if "active" in data:
                new_state = bool(data["active"])
                if new_state != self.bridge_enabled:
                    self.bridge_enabled = new_state
                    status_msg = "ENABLED" if self.bridge_enabled else "DISABLED"
                    matrix_log("comms", "smpte2138", "_on_remote_control", f"🔄 [BRIDGE] Bridge translation is now {status_msg}.", "INFO")
                    self._publish_bridge_status()
        except Exception as e:
            SMPTE2138_LOGGER.error(f"❌ [BRIDGE] Remote control failure: {e}")

    def _publish_bridge_status(self):
        """Publishes the current operational status of the bridge."""
        status_payload = {
            "active": self.bridge_enabled,
            "status": "RUNNING" if self.bridge_enabled else "STOPPED",
            "ts": time.time()
        }
        self.mqtt.publish(
            topic="OPEN-AIR/System/Status/SMPTE2138/Bridge",
            payload=orjson.dumps(status_payload).decode(),
            qos=0,
            retain=True
        )

    def _on_internal_action(self, msg):
        """Fallback handler for raw MQTT actions."""
        if not self.bridge_enabled: return
        self.handle_router_event(msg.topic, msg.payload)
