# oaComProtocols.oaComWebsocket/Core/abc.py
# Author: Gemini (Collaborator)
# Version: 20260405.1548.2

"""
Abstract base classes for transport mechanisms within oaComProtocols.oaComWebsocket.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class EventTransport(ABC):
    """Abstract base class for IS-07 event transport mechanisms."""

    def __init__(self):
        self._message_handler: Callable[[str, dict[str, Any]], None] | None = None
        self._is_connected: bool = False

    @abstractmethod
    def publish(self, topic: str, payload: dict[str, Any], retain: bool = False, qos: int = 0) -> bool:
        """Publish a message to a topic. Returns True if successful, False otherwise."""
        pass

    @abstractmethod
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """Subscribe to a topic. Returns True if successful, False otherwise."""
        pass

    @abstractmethod
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from a topic. Returns True if successful, False otherwise."""
        pass

    @abstractmethod
    def connect(self, connection_params: dict[str, Any]) -> bool:
        """Connect to the transport broker/server. Returns True if successful, False otherwise."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the transport broker/server."""
        pass

    def set_message_handler(self, handler: Callable[[str, dict[str, Any]], None]):
        """Set a callback function to handle incoming messages."""
        self._message_handler = handler

    def is_connected(self) -> bool:
        """Returns True if the transport is currently connected."""
        return self._is_connected
