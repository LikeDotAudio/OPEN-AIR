# Core/process_router_event.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Processes incoming events from the Protocol Router.

import time
from .handle_command import handle_command
from .handle_learn import handle_learn
from .handle_teach import handle_teach
from .handle_panic import handle_panic

def process_router_event(self, message):
    """
    Main entry point for events entering the Splinker module.
    RUST OPTIMIZED: Uses SplinkRegistry for matching and loop prevention.
    """
    topic = message.get("topic")
    value = message.get("value")
    timestamp = message.get("timestamp", int(time.time() * 1000))
    source = message.get("origin_source", "UNKNOWN")

    # ⚡ COMMAND INTERCEPT: System controls
    if "OPEN-AIR/System/Control/Splinker/" in topic:
        cmd_payload = {"value": value, "topic": topic, "origin_source": source}
        self._handle_command(topic, cmd_payload)
        return

    # ⚡ LEARNING MODES
    if self.learning_source:
        self._handle_learn(topic)
        return
    if self.teaching_dest:
        self._handle_teach(topic)
        return

    # ⚡ RUST OPTIMIZED LOOKUP
    matching_splinks = self.registry.get_splinks_for_topic(topic)
    
    for s in matching_splinks:
        if not s.get("active", False): continue
        
        splink_id = s["id"]

        # ⚡ FEEDBACK DETECTION (RUST)
        if self.registry.check_panic_threshold(splink_id, threshold=25):
            self._handle_panic(trigger_splink_id=splink_id)
            return

        # ⚡ LOOP PREVENTION (RUST)
        if self.registry.mark_event_processed(timestamp, topic, splink_id):
            continue

        # ⚡ EXECUTION LOCK (RUST)
        if not self.registry.try_acquire_execution_lock(splink_id):
            continue
        
        try:
            # Execute the link
            if s.get("mode") in ["BOTH", "SOURCE"]:
                self._broker_link(s, value, message)
        finally:
            self.registry.release_execution_lock(splink_id)
