# Core/splinker.py
# Author: Anthony P. Kuzub(Splinker Protocol)
# Version: 20260309.Pipeline.Modularized
#
# Description: The Central Broker for decoupled control.

import logging
import threading

try:
    from oaRustCore.oa_translator_core_rs import SplinkerLock as RustSplinkerLock
    HAS_RUST = True
except Exception as e:
    logging.warning(f"oaSplinker: Failed to load Rust SplinkerLock: {e}")
    HAS_RUST = False

class ControlBroker:
    _instance = None
    if HAS_RUST:
        _lock = RustSplinkerLock()
    else:
        _lock = threading.Lock()

    # --- Import methods from core/ sub-package ---
    from .add_monitor_callback import add_monitor_callback
    from .add_monitor_callback import add_monitor_callback as _add_monitor_callback
    from .broker_link import broker_link
    from .broker_link import broker_link as _broker_link
    from .broker_splice import broker_splice
    from .broker_splice import broker_splice as _broker_splice
    from .cancel_learning import cancel_learning
    from .cancel_learning import cancel_learning as _cancel_learning
    from .create_splink import create_splink
    from .create_splink import create_splink as _create_splink
    from .create_splink_with_params import create_splink_with_params
    from .create_splink_with_params import create_splink_with_params as _create_splink_with_params
    from .delete_splink import delete_splink
    from .delete_splink import delete_splink as _delete_splink
    from .handle_command import handle_command
    from .handle_command import handle_command as _handle_command
    from .handle_learn import handle_learn
    from .handle_learn import handle_learn as _handle_learn
    from .handle_mqtt_command import handle_mqtt_command
    from .handle_mqtt_command import handle_mqtt_command as _handle_mqtt_command
    from .handle_panic import _reset_panic, handle_panic
    from .handle_panic import handle_panic as _handle_panic
    from .handle_teach import handle_teach
    from .handle_teach import handle_teach as _handle_teach
    from .load_splinks import load_splinks
    from .load_splinks import load_splinks as _load_splinks
    from .notify_monitor import notify_monitor
    from .notify_monitor import notify_monitor as _notify_monitor
    from .parse_splink_path import parse_splink_path
    from .parse_splink_path import parse_splink_path as _parse_splink_path
    from .process_router_event import process_router_event
    from .process_router_event import process_router_event as _process_router_event
    from .publish_splinks import publish_splinks
    from .publish_splinks import publish_splinks as _publish_splinks
    from .remove_monitor_callback import remove_monitor_callback
    from .remove_monitor_callback import remove_monitor_callback as _remove_monitor_callback
    from .save_splink import save_splink
    from .save_splink import save_splink as _save_splink
    from .set_learn_mode import set_learn_mode
    from .set_learn_mode import set_learn_mode as _set_learn_mode
    from .set_teach_mode import set_teach_mode
    from .set_teach_mode import set_teach_mode as _set_teach_mode
    from .toggle_splink import toggle_splink
    from .toggle_splink import toggle_splink as _toggle_splink
    from .update_splink import update_splink
    from .update_splink import update_splink as _update_splink

    def __init__(self, state_cache_manager=None, mqtt_manager=None):
        if hasattr(self, "_initialized"): return
        self._initialized = True

        from ..Constants.constants import SPLINKER_STORAGE_PATH
        from .splink_registry import SplinkRegistry

        self.state_cache_manager = state_cache_manager
        self.mqtt_manager = mqtt_manager
        self.registry = SplinkRegistry()
        self.splink_states = {}

        self.learning_source = False
        self.teaching_dest = False
        self.active_splink_id = None

        self.storage_path = SPLINKER_STORAGE_PATH
        self._monitor_callbacks = []

        # ⚡ PANIC MODE: Emergency stop for feedback loops
        self.panic_active = False

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
