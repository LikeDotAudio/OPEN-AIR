# manifest/settle.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic for managing the 'is_settled' flag and debounce logic.

import threading
import logging
from typing import Callable, Any

try:
    from oaRustCore.oa_translator_core_rs import SettleLock as RustSettleLock
    HAS_RUST = True
except Exception as e:
    logging.warning(f"oaTranslator: Failed to load Rust SettleLock: {e}")
    HAS_RUST = False

class SettleManager:
    """
    Manages the settling logic for a control point.
    
    Provides a debounce timer that triggers a final 'is_settled: true' 
    broadcast after a period of inactivity.
    """
    def __init__(self, debounce_ms: int = 50):
        self.debounce_ms = debounce_ms
        self._timer = None
        if HAS_RUST:
            self._lock = RustSettleLock()
        else:
            self._lock = threading.Lock()

    def mark_in_motion(self, callback: Callable):
        """
        Marks the control as being in motion.
        
        Cancels any existing settle timer and prepares for a new one.
        """
        with self._lock:
            if self._timer:
                self._timer.cancel()
            
    def schedule_settle(self, callback: Callable):
        """
        Schedules a settling broadcast after inactivity.
        
        Inputs:
            callback (Callable): The function that fires the final broadcast.
        """
        with self._lock:
            if self._timer:
                self._timer.cancel()
            
            # Start a new debounce timer
            self._timer = threading.Timer(self.debounce_ms / 1000.0, callback)
            self._timer.start()
            
    def cancel(self):
        """Cancels any pending settle timer."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
