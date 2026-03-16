# workers/Splinker/splinker.py
#
# The Central Broker for decoupled control.
# Splice Control, Link Feedback.
#
# Author: Anthony P. Kuzub(Splinker Protocol)
# Version 20260309.Pipeline.Modularized

import threading
from pathlib import Path
from .constants import SPLINKER_STORAGE_PATH

class SplinkerManager:
    _instance = None
    _lock = threading.Lock()

    # --- Import methods from manager/ sub-package ---
    from .manager.add_monitor_callback import add_monitor_callback
    from .manager.remove_monitor_callback import remove_monitor_callback
    from .manager.notify_monitor import notify_monitor
    from .manager.publish_splinks import publish_splinks
    from .manager.load_splinks import load_splinks
    from .manager.save_splink import save_splink
    from .manager.handle_mqtt_command import handle_mqtt_command
    from .manager.handle_command import handle_command
    from .manager.handle_learn import handle_learn
    from .manager.handle_teach import handle_teach
    from .manager.update_splink import update_splink
    from .manager.create_splink import create_splink
    from .manager.create_splink_with_params import create_splink_with_params
    from .manager.set_learn_mode import set_learn_mode
    from .manager.set_teach_mode import set_teach_mode
    from .manager.cancel_learning import cancel_learning
    from .manager.process_router_event import process_router_event
    from .manager.parse_splink_path import parse_splink_path
    from .manager.broker_splice import broker_splice
    from .manager.broker_link import broker_link
    from .manager.delete_splink import delete_splink
    from .manager.toggle_splink import toggle_splink
    from .manager.handle_panic import handle_panic, _reset_panic

    def __init__(self, state_cache_manager=None, mqtt_manager=None):
        if hasattr(self, "_initialized"): return
        self._initialized = True
        
        self.state_cache_manager = state_cache_manager
        self.mqtt_manager = mqtt_manager
        self.splinks = []
        self.splink_states = {}
        
        self.learning_source = False
        self.teaching_dest = False
        self.active_splink_id = None
        
        self.storage_path = SPLINKER_STORAGE_PATH
        self._monitor_callbacks = []
        
        # ⚡ LOOP PREVENTION: Track processed events to break feedback cycles
        # (ts, topic, splink_id, direction) -> bool
        self.processed_events = {}
        self._cache_lock = threading.Lock()
        
        # ⚡ EXECUTION LOCKS: Prevent re-entry per splink
        self.execution_locks = {} # splink_id -> threading.Lock
        self._exec_registry_lock = threading.Lock()
        
        # ⚡ PANIC MODE: Emergency stop for feedback loops
        self.panic_active = False
        self.event_counters = {} # splink_id -> [timestamps]
        self._counter_lock = threading.Lock()
        
        self._load_splinks()

    @classmethod
    def get_instance(cls, state_cache_manager=None, mqtt_manager=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(state_cache_manager, mqtt_manager)
            else:
                # ⚡ UPDATE: If managers are provided, update the existing instance
                if state_cache_manager:
                    cls._instance.state_cache_manager = state_cache_manager
                if mqtt_manager:
                    cls._instance.mqtt_manager = mqtt_manager
        return cls._instance
