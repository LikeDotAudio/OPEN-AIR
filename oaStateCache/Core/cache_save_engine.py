# Core/cache_save_engine.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import threading
import queue
import time
from ..FileReaders import cache_io_handler

class CacheSaveEngine:
    """Implements a debounced, write-behind persistence engine for the state cache."""

    def __init__(self, cache_ref, logger, debug=True):
        self.cache = cache_ref
        self.logger = logger
        self.debug = debug
        
        self.queue = queue.Queue()
        self.pending_deltas = {}
        self.delta_lock = threading.Lock()
        
        self.last_activity_time = time.time()
        self.debounce_delay = 2.0
        self.max_stale_time = 30.0
        
        self.thread = threading.Thread(target=self._worker, daemon=True, name="StateCache_Saver")
        self.thread.start()

    def schedule_save(self, topic, payload):
        self.queue.put((topic, payload))

    def shutdown(self, timeout=2.0):
        self.queue.put(None)
        if self.thread.is_alive(): self.thread.join(timeout=timeout)

    def _worker(self):
        last_commit = time.time()
        while True:
            try:
                try:
                    item = self.queue.get(timeout=1.0)
                    if item is None: break
                    topic, payload = item
                    with self.delta_lock:
                        self.pending_deltas[topic] = payload; self.last_activity_time = time.time()
                    self.queue.task_done()
                except queue.Empty: pass

                now = time.time()
                with self.delta_lock:
                    if self.pending_deltas and (now - self.last_activity_time >= self.debounce_delay or now - last_commit >= self.max_stale_time):
                        cnt = len(self.pending_deltas)
                        self.cache.update(self.pending_deltas); self.pending_deltas.clear()
                        cache_io_handler.save_cache(self.cache); last_commit = now
                        if self.debug: self.logger.success(f"💾✍️ [CACHE] Debounced Commit: {cnt} deltas saved.")
            except Exception: self.logger.exception("🧠💾❌ [ERROR] State cache save worker failed")
