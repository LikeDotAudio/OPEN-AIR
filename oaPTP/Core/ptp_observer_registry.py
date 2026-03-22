# Core/ptp_observer_registry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger

class PTPObserverRegistry:
    """Manages the registration and notification of PTP data observers."""
    
    _observers = []

    @classmethod
    def register(cls, callback):
        if callback not in cls._observers:
            cls._observers.append(callback)
            logger.success("✅ PTP Observer registered.")

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
