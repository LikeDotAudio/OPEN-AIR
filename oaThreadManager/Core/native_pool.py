# oaThreadManager/Core/native_pool.py
# Author: Gemini Iron Oxide Architect
# Version: 20260402.0010.1
#
# Description: High-performance parallel execution engine using native Rust.

import logging

try:
    from oaRustCore.oa_thread_pool_rs import NativeThreadPool
    HAS_RUST = True
except Exception as e:
    logging.warning(f"oaThreadManager: NativeThreadPool unavailable: {e}")
    HAS_RUST = False

class NativePool:
    """
    Exposes Rayon-powered parallel processing to the OPEN-AIR system.
    Bypasses the Python GIL for numeric and data-intensive batch jobs.
    """
    def __init__(self):
        if HAS_RUST:
            self._engine = NativeThreadPool()
        else:
            self._engine = None

    def parallel_sum(self, data: list):
        if self._engine and isinstance(data, list):
            return self._engine.parallel_sum(data)
        return sum(data)

    def parallel_multiply(self, data: list, factor: float):
        if self._engine and isinstance(data, list):
            return self._engine.parallel_multiply(data, factor)
        return [x * factor for x in data]
