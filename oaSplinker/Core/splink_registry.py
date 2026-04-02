# oaSplinker/Core/splink_registry.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.2
#
# Description: Python wrapper for the Rust Splink Registry (Lock-Free).

import logging
from .oaSplinkRegistry_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from .oaSplinkRegistry_rs.oasplinkregistry_rs import SplinkRegistry as RustSplinkRegistry
    HAS_RUST = True
except Exception as e:
    logging.error(f"oaSplinker: Failed to load Rust Splink Registry: {e}")
    HAS_RUST = False

LOCAL_DEBUG = False

class SplinkRegistry:
    """
    High-performance concurrent registry for Splinks using Rust DashMap.
    """
    def __init__(self):
        if HAS_RUST:
            if LOCAL_DEBUG:
                print("🔗🛠️🔗 [SPLINKER] Using PURE RUST registry.")
            self._registry = RustSplinkRegistry()
        else:
            self._registry = None
            logging.error("oaSplinker: Missing mandatory Rust registry.")

    def add_splink(self, topic: str, splink: dict):
        if self._registry:
            self._registry.add_splink(topic, splink)

    def get_splinks_for_topic(self, topic: str):
        if self._registry:
            return self._registry.get_splinks_for_topic(topic)
        return []

    def all_splinks(self):
        if self._registry:
            return self._registry.all_splinks()
        return []

    def get_splink_by_id(self, splink_id: str):
        if self._registry:
            return self._registry.get_splink_by_id(splink_id)
        return None

    def update_splink(self, splink_id: str, new_data: dict):
        if self._registry:
            self._registry.update_splink(splink_id, new_data)

    def delete_splink(self, splink_id: str):
        if self._registry:
            self._registry.delete_splink(splink_id)

    def try_acquire_execution_lock(self, splink_id: str) -> bool:
        if self._registry:
            return self._registry.try_acquire_execution_lock(splink_id)
        return True # Fallback to unsafe

    def release_execution_lock(self, splink_id: str):
        if self._registry:
            self._registry.release_execution_lock(splink_id)

    def mark_event_processed(self, ts_ms: int, topic: str, splink_id: str) -> bool:
        if self._registry:
            return self._registry.mark_event_processed(ts_ms, topic, splink_id)
        return False

    def check_panic_threshold(self, splink_id: str, threshold: int) -> bool:
        if self._registry:
            return self._registry.check_panic_threshold(splink_id, threshold)
        return False

    def clear(self):
        if self._registry:
            self._registry.clear()

    def topics(self):
        if self._registry:
            return self._registry.topics()
        return []

    def __len__(self):
        if self._registry:
            return self._registry.len()
        return 0
