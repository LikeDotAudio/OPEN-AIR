# Methods/debounce_handler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import time

from .base_handler import BaseHandler


class DebounceHandler(BaseHandler):
    """
    Prevents rapid-fire messages by enforcing a cooldown period.
    NOTE: This handler needs to maintain state across multiple invocations, 
          so its state should be managed by the SplinkManager.
    """
    def execute(self, value, splink=None, state=None, direction="FORWARD"):
        period_ms = self.params.get("period_ms", 50)

        last_execution_time = state.get("last_debounce_time", 0)

        current_time = time.time() * 1000
        if current_time - last_execution_time < period_ms:
            return None # Drop the message

        state["last_debounce_time"] = current_time
        return value
