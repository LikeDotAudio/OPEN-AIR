from collections.abc import Callable
from typing import Any

from aes70.types.ocaevent import OcaEvent


class BaseEvent:
    def __init__(self, obj: Any, id: int, argument_types: list[type]):
        self.object = obj
        self.id = id
        self.handlers: set[Callable] = set()
        self.result = None
        self.argument_types = argument_types

    def get_oca_event(self) -> OcaEvent:
        return OcaEvent(self.object.ObjectNumber, self.id)

    def do_subscribe(self):
        pass

    def do_unsubscribe(self):
        pass

    def subscribe(self, callback: Callable) -> bool:
        self.handlers.add(callback)

        if len(self.handlers) == 1:
            self.result = self.do_subscribe()
            self.result = None
            return True

        if self.result is not None:
            return self.result

        return True

    def unsubscribe(self, callback: Callable) -> bool:
        self.handlers.discard(callback)

        if not self.handlers:
            try:
                self.do_unsubscribe()
            except Exception:
                pass

        return True

    def dispose(self):
        self.handlers.clear()

        if self.handlers:
            try:
                self.do_unsubscribe()
            except Exception:
                pass



