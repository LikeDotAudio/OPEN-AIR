# Core/ptp_observer_registry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect

from oaLogging.Methods.matrix_gate import matrix_log


class PTPObserverRegistry:
    """Manages the registration and notification of PTP data observers."""

    _observers = []

    @classmethod
    def register(cls, callback):
        if callback not in cls._observers:
            cls._observers.append(callback)
            matrix_log("CORE", "PTP", inspect.currentframe().f_code.co_name, "✅ PTP Observer registered.", level="SUCCESS")

    @classmethod
    def unregister(cls, callback):
        if callback in cls._observers:
            cls._observers.remove(callback)

    @classmethod
    def notify(cls, data):
        """Distributes data to all registered callbacks."""
        for cb in cls._observers:
            try: cb(data)
            except: pass
