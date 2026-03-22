# Core/remove_monitor_callback.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

def remove_monitor_callback(self, callback):
    if callback in self._monitor_callbacks:
        self._monitor_callbacks.remove(callback)
