# oaTranslator/Core/task_pool.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2350.1
#
# Description: Python wrapper for the Rust Rayon Task Pool.

import logging
import multiprocessing
from .oaTaskPool_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from .oaTaskPool_rs.oataskpool_rs import TaskPool as RustTaskPool
    HAS_RUST = True
except Exception as e:
    logging.error(f"oaTranslator: Failed to load Rust Task Pool: {e}")
    HAS_RUST = False

class TaskPool:
    """
    High-performance work-stealing task pool using Rust Rayon.
    """
    def __init__(self, num_threads=None):
        if num_threads is None:
            num_threads = multiprocessing.cpu_count()
            
        if HAS_RUST:
            print(f"⚙️🛠️🔗 [TRANSLATOR] Using PURE RUST task pool ({num_threads} threads).")
            self._pool = RustTaskPool(num_threads)
        else:
            self._pool = None
            logging.error("oaTranslator: Missing mandatory Rust task pool.")

    def spawn(self, callback):
        if self._pool:
            self._pool.spawn(callback)

    def par_map(self, data: list, callback):
        if self._pool:
            return self._pool.par_map(data, callback)
        return [callback(item) for item in data]
