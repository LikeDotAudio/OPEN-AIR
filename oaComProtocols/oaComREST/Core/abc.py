# oaComProtocols/oaComREST/Core/abc.py
# Author: Gemini (Collaborator)
# Version: 20260414.2000.1
#
# Description: Abstract base classes for REST transport mechanisms.

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class EventTransport(ABC):
    """Abstract base class for event transport mechanisms."""

    def __init__(self):
        self._message_handler: Callable[[str, Any], None] | None = None
        self._is_connected: bool = False

    @abstractmethod
    def publish(self, topic: str, payload: Any, retain: bool = False, qos: int = 0) -> bool:
        pass

    @abstractmethod
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        pass

    @abstractmethod
    def unsubscribe(self, topic: str) -> bool:
        pass

    @abstractmethod
    def connect(self, connection_params: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    def set_message_handler(self, handler: Callable[[str, Any], None]):
        self._message_handler = handler

    def is_connected(self) -> bool:
        return self._is_connected
