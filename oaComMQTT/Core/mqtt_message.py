# mqtt/mqtt_message.py
#
# Defines the standardized MqttMessage dataclass for the application.
# Enforces strict typing for all MQTT traffic between partitions.
#
# Author: Anthony P. Kuzub(Refactored)
# Version 20260221.1

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union, List
import orjson

@dataclass(frozen=True)
class MqttMessage:
    """
    Standardized MQTT message container.
    Frozen to ensure immutability as it passes through the system.
    """
    topic: str
    payload: Union[str, bytes, Dict[str, Any], List[Any]]
    qos: int = 0
    retain: bool = False
    
    def decode_payload(self) -> str:
        """Helper to ensure payload is a string."""
        if isinstance(self.payload, bytes):
            return self.payload.decode("utf-8")
        if isinstance(self.payload, (dict, list)):
            return orjson.dumps(self.payload).decode().decode("utf-8")
        return str(self.payload)

    def get_json_payload(self) -> Union[Dict[str, Any], List[Any]]:
        """Helper to ensure payload is a dictionary or list (parsed JSON)."""
        if isinstance(self.payload, (dict, list)):
            return self.payload
        
        decoded = self.decode_payload()
        try:
            return orjson.loads(decoded)
        except orjson.JSONDecodeError:
            # Fallback for non-JSON payloads
            return {"val": decoded}

    def to_dict(self) -> Dict[str, Any]:
        """Converts to a dictionary for publishing."""
        return {
            "topic": self.topic,
            "payload": self.payload,
            "qos": self.qos,
            "retain": self.retain
        }
