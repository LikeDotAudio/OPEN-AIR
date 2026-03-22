# Core/sync_queue_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import queue
import threading
import tkinter as tk
from loguru import logger

class SyncQueueMixin:
    """Manages the UI update queue and the background registration worker."""

    def _initialize_queues(self):
        self._registration_queue = queue.Queue()
        self.update_queue = queue.Queue()
        self._processing_scheduled = False
        self._schedule_lock = threading.Lock()
        
        self._reg_thread = threading.Thread(target=self._registration_worker, daemon=True)
        self._reg_thread.start()

    def _registration_worker(self):
        while True:
            widget_id = self._registration_queue.get()
            if widget_id is None: break
            self.initialize_widget_state(widget_id)
            self._registration_queue.task_done()

    def _schedule_queue_processing(self):
        if getattr(self, 'is_inert', True): return
        with self._schedule_lock:
            if getattr(self, '_processing_scheduled', False): return
            self._processing_scheduled = True
        self.root.after(0, self._process_queue_wrapper)

    def _process_queue_wrapper(self):
        with self._schedule_lock:
            self._processing_scheduled = False
        self._process_queue()

    def _process_queue(self):
        if getattr(self, 'is_inert', True): return
        count = 0
        while count < 1000:
            try:
                tk_var, value, widget_id = self.update_queue.get_nowait()
                count += 1
                try:
                    if tk_var.get() == value: continue
                except tk.TclError as e:
                    # Specific exception for Tkinter errors to avoid masking underlying issues
                    logger.warning(f"⚠️ [GUI] Failed to read tk_var for widget_id {widget_id}: {e}")
                    continue

                self._silent_update = True
                try: tk_var.set(value)
                finally: self._silent_update = False
            except queue.Empty: break
        
        if not self.update_queue.empty():
            self._schedule_queue_processing()
