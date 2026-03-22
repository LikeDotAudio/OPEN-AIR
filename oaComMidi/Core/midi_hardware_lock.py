# Core/midi_hardware_lock.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import threading
import time

class MIDIHardwareLock:
    """Thread-safe management of hardware interaction locks."""

    def __init__(self):
        self._locked_params = set()
        self._mutex = threading.Lock()

    def lock(self, topic):
        with self._mutex: self._locked_params.add(topic)

    def unlock(self, topic):
        with self._mutex:
            if topic in self._locked_params: self._locked_params.remove(topic)

    def is_locked(self, topic):
        with self._mutex: return topic in self._locked_params

    def delayed_unlock(self, topic, delay=0.5):
        def _task():
            time.sleep(delay)
            self.unlock(topic)
        import threading
        threading.Thread(target=_task, daemon=True).start()
