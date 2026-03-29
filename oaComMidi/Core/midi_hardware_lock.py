# oaComMidi/Core/midi_hardware_lock.py
#
# Thread-safe management of hardware interaction locks.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1415.1

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
