# workers/Command_Router/protocol_router/settle.py
#
# Interaction Locking and Parameter Settling Logic.
# 
# Prevents feedback loops by rejecting self-reflections while a parameter
# is actively being modified by a human or a high-frequency stream.

import threading
import time
from .constants import LOCAL_DEBUG
from oaLogging.logger import router_logger

class SettleManager:
    """
    Manages interaction locks and terminal state 'settling' for topics.
    """
    def __init__(self, ingest_callback):
        self._ingest_callback = ingest_callback
        self._settle_timers = {}
        self._settle_lock = threading.Lock()
        self._locked_params_by_instance = {} # instance_id -> set(topics)

    def is_parameter_locked(self, topic, instance_id=None):
        """Checks if a topic is currently locked, globally or for an instance."""
        with self._settle_lock:
            if instance_id:
                locked_set = self._locked_params_by_instance.get(instance_id, set())
                return topic in locked_set
            else:
                for locked_set in self._locked_params_by_instance.values():
                    if topic in locked_set:
                        return True
        return False

    def lock_parameter(self, topic, instance_id):
        """Engages an interaction lock for a specific topic/instance."""
        with self._settle_lock:
            if instance_id not in self._locked_params_by_instance:
                self._locked_params_by_instance[instance_id] = set()
            self._locked_params_by_instance[instance_id].add(topic)

    def unlock_parameter(self, topic, instance_id):
        """Releases an interaction lock."""
        with self._settle_lock:
            locked_set = self._locked_params_by_instance.get(instance_id)
            if locked_set and topic in locked_set:
                locked_set.remove(topic)
                if not locked_set:
                    del self._locked_params_by_instance[instance_id]

    def schedule_settling(self, topic, original_msg):
        """
        Schedules a terminal LINK_FEEDBACK after a period of silence.
        """
        # Cancel previous timer for this topic if it exists.
        with self._settle_lock:
            if topic in self._settle_timers:
                self._settle_timers[topic].cancel()
        
        # Prepare final settling callback.
        def _fire_settled():
            settled_meta = original_msg["meta"].copy()
            settled_meta["msg_type"] = "LINK_FEEDBACK"
            settled_meta["is_settled"] = True
            
            if LOCAL_DEBUG:
                router_logger.debug(
                    f"⏳⏳🔄 [ROUTER] Settling: Firing final "
                    f"LINK_FEEDBACK for {topic}"
                )
            
            # Unlock parameter.
            self.unlock_parameter(topic, original_msg.get("full_id"))
            
            # Re-ingest as settled to inform all spokes.
            self._ingest_callback("SYSTEM", topic, original_msg["val"], settled_meta)
            
            # Clean up the timer reference.
            with self._settle_lock:
                if self._settle_timers.get(topic) == t:
                    del self._settle_timers[topic]
        
        # 50ms silence required to consider a parameter 'settled'.
        t = threading.Timer(0.050, _fire_settled)
        
        with self._settle_lock:
            self._settle_timers[topic] = t
            
        t.start()
