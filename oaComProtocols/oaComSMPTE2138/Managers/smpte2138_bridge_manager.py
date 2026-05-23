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

import sys
import threading
import time
from pathlib import Path

import orjson

from oaLogging.Core.logger import SMPTE2138_LOGGER

logger = SMPTE2138_LOGGER.bind(protocol="SMPTE2138")

# --- Path Guard for Protobuf Imports ---
interface_path = Path(__file__).resolve().parents[1] / "Interface"
if str(interface_path) not in sys.path:
    sys.path.insert(0, str(interface_path))

# --- Protobuf Imports ---
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaComProtocols.oaComSMPTE2138.Interface import param_pb2

# --- Standard OPEN-AIR Imports ---
from oaLogging.Core.logger import SMPTE2138_LOGGER
from oaLogging.Methods.matrix_gate import matrix_log


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
        self._running = False
        self._watchdog_thread = None

        # Internal OID mapping
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

        matrix_log("comms", "smpte2138", "__init__", "✅ [BRIDGE] SMPTE2138 Protocol Bridge initialized.", "SUCCESS")

    def start(self):
        """Standardized entry point for the ProtocolRouter to activate the bridge."""
        if self._running: return
        self._running = True
        self.bridge_enabled = True

        # ⚡ WATCHDOG: Ensures the engine stays alive and fights for connectivity
        self._watchdog_thread = threading.Thread(target=self._auto_start_watchdog, daemon=True, name="ST2138-Watchdog")
        self._watchdog_thread.start()

        matrix_log("comms", "smpte2138", "start", "▶️ [BRIDGE] SMPTE2138 Protocol Bridge started (FIGHTING FOR LIFE).", "INFO")
        self._publish_bridge_status()

    def stop(self):
        """Standardized entry point for the ProtocolRouter to deactivate the bridge."""
        self._running = False
        self.bridge_enabled = False
        matrix_log("comms", "smpte2138", "stop", "⏹️ [BRIDGE] SMPTE2138 Protocol Bridge stopping...", "INFO")
        self._publish_bridge_status()

    def _auto_start_watchdog(self):
        """Ensures the bridge is always enabled and publishing status."""
        while self._running:
            try:
                if not self.bridge_enabled:
                    # The engine 'fights' to stay alive as long as python is running
                    self.bridge_enabled = True
                    matrix_log("comms", "smpte2138", "_watchdog", "🛡️ [BRIDGE] Watchdog forced bridge reactivation.", "WARNING")
                    self._publish_bridge_status()

                # Periodic status broadcast
                # Actual publication is handled inside the 'if' above or via status loop
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
            time.sleep(5.0) # Check every 5 seconds for more aggressive uptime

    def _setup_subscriptions(self):
        """Registers listeners for internal actions and remote control."""
        # 1. Action Triggers (Raw MQTT fallback / Broad Subscription)
        # We subscribe to the root namespace to ensure
        # that we catch ALL changes even if the ProtocolRouter dispatch is gated.
        self.router.subscribe_to_topic("OPEN-AIR/#", self._on_internal_action)

        # 2. Remote Bridge Control (from GUI)
        self.router.subscribe_to_topic("OPEN-AIR/System/Control/SMPTE2138/Bridge", self._on_remote_control)

        matrix_log("comms", "smpte2138", "_setup_subscriptions", "👂 [LISTEN] Bridge active and listening for OPEN-AIR/# Actions and Control.", "DEBUG")


    def handle_router_event(self, topic, value, meta=None):
        """
        Direct entry point from ProtocolRouter dispatch.
        Bypasses raw MQTT subscription for higher reliability.
        """
        # ⚡ DEBUG: Log arrival of event
        if _is_debug():
            matrix_log("comms", "smpte2138", "handle_router_event", f"📥 [ST2138-IN] topic={topic} enabled={self.bridge_enabled}", "TRACE")

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
        # If value is a dict, extract the primary numeric or boolean value.
        real_val = value
        if isinstance(value, dict) and "value" in value:
            real_val = value["value"]
            # Merge dictionary into metadata if it's not already there
            meta = meta or {}
            for k, v in value.items():
                if k != "value": meta[k] = v

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

        # ⚡ DEBUG: Log resolved OID
        if _is_debug():
            val_str = str(real_val)[:100] + ("..." if len(str(real_val)) > 100 else "")
            matrix_log("comms", "smpte2138", "handle_router_event", f"📝 [ST2138-OID] oid={oid} value={val_str} type={type(real_val)}", "DEBUG")

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
        if _is_debug():
            val_str = str(value)[:100] + ("..." if len(str(value)) > 100 else "")
            matrix_log("comms", "smpte2138", "_publish_parameter", f"📡📤📤 [SMPTE2138] Published FLOAT32 to {smpte2138_topic} ({val_str})", "DEBUG")

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
        if _is_debug():
            val_str = str(value)[:100] + ("..." if len(str(value)) > 100 else "")
            matrix_log("comms", "smpte2138", "_publish_command", f"🚀📤📤 [SMPTE2138] Published COMMAND to {smpte2138_topic} ({val_str})", "DEBUG")

    def _on_remote_control(self, message):
        """Processes remote start/stop commands."""
        try:
            if not message.payload: return
            data = message.get_json_payload()

            if "active" in data:
                new_state = bool(data["active"])

                # 🛡️ RESILIENCE: If it's a retained message and it's trying to disable us,
                # we ignore it to ensure we start in an ACTIVE state.
                if message.retain and not new_state:
                    matrix_log("comms", "smpte2138", "_on_remote_control", "🛡️ [BRIDGE] Ignoring retained DISABLE command on startup.", "DEBUG")
                    return

                if new_state != self.bridge_enabled:
                    self.bridge_enabled = new_state
                    status_message = "ENABLED" if self.bridge_enabled else "DISABLED"
                    matrix_log("comms", "smpte2138", "_on_remote_control", f"🔄 [BRIDGE] Bridge translation is now {status_message}.", "INFO")
                    self._publish_bridge_status()
        except Exception as e:
            SMPTE2138_LOGGER.error(f"❌ [BRIDGE] Remote control failure: {e}")

    def _publish_bridge_status(self):
        """Publishes the current operational status of the bridge."""
        status_payload = {
            "active": self.bridge_enabled,
            "status": "RUNNING" if self.bridge_enabled else "STOPPED",
            "timestamp": time.time()
        }
        self.mqtt.publish(
            topic="OPEN-AIR/System/Status/SMPTE2138/Bridge",
            payload=orjson.dumps(status_payload).decode(),
            qos=0,
            retain=True
        )

    def _on_internal_action(self, message):
        """Fallback handler for raw MQTT actions."""
        if not self.bridge_enabled: return

        # ⚡ V3.1.22 FEEDBACK LOOP PREVENTION:
        # Ignore messages that are explicitly linked feedback to prevent loops.
        try:
            if not message.payload: return
            data = message.get_json_payload()

            # Extract actual value if it's a dict
            value = data
            meta = {}
            if isinstance(data, dict):
                if data.get("message_type") == "LINK_FEEDBACK":
                    return
                value = data.get("value", data)
                meta = data

            self.handle_router_event(message.topic, value, meta)
        except Exception as e:
            SMPTE2138_LOGGER.error(f"❌ [BRIDGE] MQTT Internal action handling failure: {e}")
