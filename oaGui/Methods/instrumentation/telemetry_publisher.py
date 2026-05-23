# oaGui/Methods/telemetry_publisher.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles MQTT publishing for UI telemetry data.

import time

import orjson

from oaComProtocols.oaComMQTT.Core.mqtt_publisher_service import is_connected


class TelemetryPublisher:
    """
    Handles MQTT publishing for UI telemetry data.
    """
    @staticmethod
    def publish_visibility(engine, topic, tab_name, is_visible):
        """Publishes visibility status to MQTT."""
        if not is_connected(): return
        payload = {
            "visible": is_visible,
            "timestamp": time.time(),
            "tab_name": tab_name,
        }
        engine.publish_command(topic, orjson.dumps(payload).decode())

    @staticmethod
    def publish_geometry(engine, topic, tab_name, geometry):
        """Publishes geometry data to MQTT."""
        if not is_connected(): return
        w, h, x, y = geometry
        payload = {
            "width": w, "height": h, "x": x, "y": y,
            "timestamp": time.time(),
            "tab_name": tab_name,
        }
        engine.publish_command(topic, orjson.dumps(payload).decode())
