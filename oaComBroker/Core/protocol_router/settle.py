# Core/protocol_router/settle.py
#
# Interaction Locking and Parameter Settling Logic for the Protocol Router.
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
# Version 20260328.1425.1
#
# Description:
# This module implements "Parameter Settling" and "Interaction Locking."
# These mechanisms prevent feedback loops and jitter when a user is actively
# modifying a parameter on a physical control surface or UI. It ensures that
# the system reaches a stable terminal state after a burst of activity.
#
# Architectural Role:
# - Prevents self-reflection loops at the router level.
# - Implements a temporal "dead-zone" during active user interaction.
# - Triggers final state synchronization (LINK_FEEDBACK) after silence.

import threading
import time
from .constants import LOCAL_DEBUG
from oaLogging.Core.logger import router_logger

class SettleManager:
    """
    Manages interaction locks and terminal state 'settling' for topics.
    
    The SettleManager tracks which parameters are currently being manipulated
    by which instance. It uses threading.Timer objects to detect periods of
    inactivity and broadcast final "settled" messages.
    """
    def __init__(self, ingest_callback):
        """
        Initializes the SettleManager with a reference to the router's ingest.
        
        Args:
            ingest_callback (fn): The router.ingest function for re-injection.
        """
        self._ingest_callback = ingest_callback
        self._settle_timers = {}
        self._settle_lock = threading.Lock()
        self._locked_params_by_instance = {} # instance_id -> set(topics)

    def is_parameter_locked(self, topic, instance_id=None):
        """
        Checks if a topic is currently locked, globally or for an instance.
        
        Args:
            topic (str): The logical address to check.
            instance_id (str, optional): The GUID of a specific instance.
            
        Returns:
            bool: True if locked, False otherwise.
        """
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
        """
        Engages an interaction lock for a specific topic/instance.
        
        Args:
            topic (str): The parameter to lock.
            instance_id (str): The GUID of the instance claiming the lock.
        """
        with self._settle_lock:
            if instance_id not in self._locked_params_by_instance:
                self._locked_params_by_instance[instance_id] = set()
            self._locked_params_by_instance[instance_id].add(topic)

    def unlock_parameter(self, topic, instance_id):
        """
        Releases an interaction lock.
        
        Args:
            topic (str): The parameter to unlock.
            instance_id (str): The GUID of the instance releasing the lock.
        """
        with self._settle_lock:
            locked_set = self._locked_params_by_instance.get(instance_id)
            if locked_set and topic in locked_set:
                locked_set.remove(topic)
                if not locked_set:
                    del self._locked_params_by_instance[instance_id]

    def schedule_settling(self, topic, original_msg):
        """
        Schedules a terminal LINK_FEEDBACK after a period of silence.
        
        This method is called for every SPLICE_ACTION. It resets a 50ms 
        timer; if the timer expires without being reset, a terminal
        message is broadcast to confirm the final parameter state.
        
        Args:
            topic (str): The parameter to settle.
            original_msg (dict): The last message received for this topic.
        """
        # Atomically cancel any existing timer for this specific topic.
        with self._settle_lock:
            if topic in self._settle_timers:
                self._settle_timers[topic].cancel()
        
        # Prepare the final settling callback task.
        def _fire_settled():
            settled_meta = original_msg["meta"].copy()
            settled_meta["msg_type"] = "LINK_FEEDBACK"
            settled_meta["is_settled"] = True
            
            if LOCAL_DEBUG:
                router_logger.debug(
                    f"⏳⏳🔄 [ROUTER] Settling: Firing final "
                    f"LINK_FEEDBACK for {topic}"
                )
            
            # Unlock the parameter before re-ingesting to allow the feedback 
            # packet to pass through the router's filters.
            self.unlock_parameter(topic, original_msg.get("full_id"))
            
            # Re-ingest the message as "settled" to inform all network spokes.
            self._ingest_callback("SYSTEM", topic, original_msg["val"], settled_meta)
            
            # Cleanup the internal timer reference.
            with self._settle_lock:
                if self._settle_timers.get(topic) == t:
                    del self._settle_timers[topic]
        
        # 50ms of silence is required to consider an interaction "settled."
        t = threading.Timer(0.050, _fire_settled)
        
        with self._settle_lock:
            self._settle_timers[topic] = t
            
        t.start()
