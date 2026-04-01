# Core/work_stealing_pool.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: High-performance Task Pool using Rust Rayon (RUST OPTIMIZED).

from .task_pool import TaskPool
import time

class WorkStealingPool:
    """
    A high-performance thread pool implementing a work-stealing algorithm in Rust.
    MANDATORY Rust implementation for true parallelism.
    """
    def __init__(self, num_workers=None):
        self._pool = TaskPool(num_threads=num_workers)

    def apply_batch(self, tasks):
        """
        Submits a batch of tasks. 
        Tasks should be [(func, args, kwargs), ...]
        Returns a list of results.
        """
        results = []
        
        # Helper to execute and append to closure-captured list
        def _exec_task(task_data):
            func, args, kwargs = task_data
            return func(*args, **kwargs)

        # Use Rust parallel map for execution
        return self._pool.par_map(tasks, _exec_task)

    def spawn(self, callback):
        """Spawns a single fire-and-forget task."""
        self._pool.spawn(callback)

    def shutdown(self):
        # Rayon handles shutdown via drop in Rust
        pass
