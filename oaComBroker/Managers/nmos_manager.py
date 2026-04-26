# oaComBroker/Managers/nmos_manager.py
#
# Orchestrates NMOS IS-07 Event & Tally bridging.
# Routes internal router events to NMOS IS-07 WebSocket/MQTT transports.
#
# Author: Gemini (Collaborator)
# Version: 20260407.0045.1

from oaComProtocols.oaComNmos.IS07.core_models import Identity, Timing
from oaComProtocols.oaComNmos.IS07.transports import Is07Bridge
from oaLogging.Methods.matrix_gate import matrix_log


class NmosManager:
    """
    Bridge between the Protocol Router and the NMOS IS-07 Transport.
    """
    def __init__(self, registrar_url="http://localhost:4000"):
        self.bridge = Is07Bridge(registrar_url)
        self._is_running = False

    def start(self):
        if self._is_running: return
        # In a real scenario, we'd fetch these from a central config or discovery service
        connection_params_mqtt = {
            "destination_host": "localhost",
            "destination_port": 1883,
            "broker_protocol": "mqtt"
        }
        connection_params_ws = {
            "destination_host": "localhost",
            "destination_port": 8080
        }

        try:
            self.bridge.initialize_transports(connection_params_mqtt, connection_params_ws)
            self._is_running = True
            matrix_log("comms", "nmos", "start", "✅ NMOS IS-07 Bridge Started.", "SUCCESS")
        except Exception as e:
            matrix_log("comms", "nmos", "start", f"❌ Failed to start NMOS Bridge: {e}", "ERROR")

    def stop(self):
        if not self._is_running: return
        self.bridge.shutdown()
        self._is_running = False
        matrix_log("comms", "nmos", "stop", "⏹️ NMOS IS-07 Bridge Stopped.", "INFO")

    def handle_router_event(self, topic, value, meta):
        """
        Translates internal Protocol Router events to NMOS IS-07 state changes.
        """
        if not self._is_running: return

        # ⚡ MAPPING LOGIC: Map internal topics to NMOS Identities
        # This is a basic implementation; a real one would use a registry.
        identity = Identity(
            source_id=meta.get("source_id", "00000000-0000-0000-0000-000000000000"),
            flow_id=meta.get("flow_id", "00000000-0000-0000-0000-000000000000")
        )
        timing = Timing(
            creation_timestamp=meta.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
            origin_timestamp=meta.get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        )

        # Determine event type based on value
        if isinstance(value, bool):
            etype = "boolean"
        elif isinstance(value, (int, float)):
            etype = "number"
        else:
            etype = "string"

        # ⚡ NMOS BRIDGE: Publish via WebSocket (preferred for IS-07) and MQTT
        self.bridge.publish_state_change(
            identity=identity,
            timing=timing,
            event_type=etype,
            payload=value,
            transport_topic=topic,
            transport_type="websocket"
        )

        self.bridge.publish_state_change(
            identity=identity,
            timing=timing,
            event_type=etype,
            payload=value,
            transport_topic=topic,
            transport_type="mqtt"
        )

import time
