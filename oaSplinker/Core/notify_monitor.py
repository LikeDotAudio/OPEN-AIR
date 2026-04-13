# Core/notify_monitor.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from ..Constants.constants import splinker_logger

def notify_monitor(self, message_type, data):
    for cb in self._monitor_callbacks:
        try:
            cb(message_type, data)
        except Exception as e:
            splinker_logger.error(f"Splinker monitor callback error: {e}")
