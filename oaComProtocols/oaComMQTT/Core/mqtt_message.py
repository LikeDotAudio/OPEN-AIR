# Core/mqtt_message.py
# Author: Anthony P. Kuzub(Refactored)
# Version: 20260221.1
#
# Description: Defines the standardized MqttMessage dataclass for the application.

from dataclasses import dataclass
from typing import Any

import orjson


@dataclass(frozen=True)
class MqttMessage:
    """
    Standardized MQTT message container.
    Frozen to ensure immutability as it passes through the system.
    """
    topic: str
    payload: str | bytes | dict[str, Any] | list[Any]
    qos: int = 0
    retain: bool = False

    def decode_payload(self) -> str:
        """
        Helper to ensure payload is a string.
        ⚡ STABILITY: Uses a tiered fallback for non-UTF-8 byte sequences.
        """
        if isinstance(self.payload, bytes):
            try:
                return self.payload.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to latin-1 which accepts all byte values
                return self.payload.decode("latin-1")
        if isinstance(self.payload, (dict, list)):
            return orjson.dumps(self.payload).decode("utf-8")
        return str(self.payload)

    def get_json_payload(self) -> dict[str, Any] | list[Any]:
        """Helper to ensure payload is a dictionary or list (parsed JSON)."""
        if isinstance(self.payload, (dict, list)):
            return self.payload

        decoded = self.decode_payload()
        try:
            return orjson.loads(decoded)
        except orjson.JSONDecodeError:
            # Fallback for non-JSON payloads
            return {"value": decoded}

    def to_dict(self) -> dict[str, Any]:
        """Converts to a dictionary for publishing."""
        return {
            "topic": self.topic,
            "payload": self.payload,
            "qos": self.qos,
            "retain": self.retain
        }
