# oaLogging/Workers/batch_sink.py
# Author: Gemini (Collaborator)
# Version: 20260413.1000.1
#
# Description: High-Performance Batch Logging Sink for OPEN-AIR.

import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from oaLogging.Constants.logging_constants import DEFAULT_BATCH_SIZE, DEFAULT_FLUSH_INTERVAL
from oaLogging.Core.rust_sink_bridge import get_rust_sink, has_rust_sink

class BatchLogSink:
    """
    ⚡ HIGH PERFORMANCE SINK: Caches logs in memory and writes in batches.
    Reduces I/O overhead and lock contention on the hot path.
    Now supports Native Rust Asynchronous offloading.
    """
    def __init__(self, file_path_pattern, format_str, batch_size=DEFAULT_BATCH_SIZE, interval=DEFAULT_FLUSH_INTERVAL):
        self.file_path_pattern = file_path_pattern # Now a pattern with {time}
        self.format_str = format_str
        self.batch_size = batch_size
        self.interval = interval
        self.buffer = deque()
        self._lock = threading.RLock()
        self._is_running = True
        self._current_file = None
        self._current_minute = ""
        
        if not has_rust_sink():
            # Start the background flusher thread if Rust is unavailable.
            self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True, name=f"LogBatchFlusher-{os.path.basename(file_path_pattern)}")
            self._flush_thread.start()

    def _get_current_file(self):
        """Calculates the target filename for the current minute (YYYYMMDDHHMM)."""
        now = datetime.now()
        minute_str = now.strftime("%Y%m%d%H%M")
        
        if minute_str != self._current_minute:
            self._current_minute = minute_str
            # Pattern expected like ".../Application_{time}.log"
            self._current_file = self.file_path_pattern.replace("{time}", minute_str)
            # Ensure directory exists for new minute file
            os.makedirs(os.path.dirname(self._current_file), exist_ok=True)
            
        return self._current_file

    def write(self, message):
        """Standard Loguru sink write method."""
        rust_sink = get_rust_sink()
        if rust_sink:
            # Direct handoff to Rust for non-blocking I/O
            rust_sink.write(str(self._get_current_file()), str(message))
            return

        with self._lock:
            self.buffer.append(message)
            if len(self.buffer) >= self.batch_size:
                self._trigger_flush()

    def _trigger_flush(self):
        """Internal helper to write the buffer to disk."""
        if not self.buffer:
            return
            
        target_file = self._get_current_file()
            
        with self._lock:
            lines_to_write = list(self.buffer)
            self.buffer.clear()
            
        try:
            with open(target_file, "a", encoding="utf-8") as f:
                f.writelines(lines_to_write)
        except Exception as e:
            # This critical error should always be visible
            print(f"CRITICAL: Log batch write to {target_file} failed: {e}", file=sys.stderr)

    def _flush_loop(self):
        """Background thread to ensure logs are flushed periodically."""
        while self._is_running:
            try:
                time.sleep(self.interval)
                self._trigger_flush()
            except Exception as e:
                # Use sys.stderr for flusher thread error reports
                print(f"CRITICAL: Log flush loop error for {self.file_path_pattern}: {e}", file=sys.stderr)

    def stop(self):
        """Stops the flusher thread and flushes remaining logs."""
        self._is_running = False
        self._trigger_flush()
