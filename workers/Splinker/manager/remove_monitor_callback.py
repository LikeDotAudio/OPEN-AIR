def remove_monitor_callback(self, callback):
    if callback in self._monitor_callbacks:
        self._monitor_callbacks.remove(callback)
