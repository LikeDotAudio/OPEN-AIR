# Core/work_stealing_pool.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import collections
import threading
import time
import random
from loguru import logger

class WorkStealingQueue:
    """A thread-safe deque that supports local LIFO and remote FIFO stealing."""
    def __init__(self):
        self.deque = collections.deque()
        self.lock = threading.Lock()

    def push_task(self, task):
        with self.lock:
            self.deque.append(task)

    def pop_local_task(self):
        """Local worker pops from the right (LIFO) for cache locality."""
        with self.lock:
            if self.deque:
                return self.deque.pop()
            return None

    def steal(self):
        """Remote stealer pops from the left (FIFO) to get older/larger tasks."""
        with self.lock:
            if self.deque:
                return self.deque.popleft()
            return None
    
    def __len__(self):
        return len(self.deque)

class WorkStealingPool:
    """
    A lightweight thread pool implementing a work-stealing algorithm.
    Optimized for short-lived PIL/NumPy tasks that release the GIL.
    """
    def __init__(self, num_workers=4):
        self.num_workers = num_workers
        self.queues = [WorkStealingQueue() for _ in range(num_workers)]
        self.threads = []
        self._shutdown = False
        
        for i in range(num_workers):
            t = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            t.start()
            self.threads.append(t)

    def _worker_loop(self, worker_id):
        my_queue = self.queues[worker_id]
        
        while not self._shutdown:
            # 1. Try local queue (LIFO)
            task = my_queue.pop_local_task()
            
            # 2. If empty, try stealing from neighbors (FIFO)
            if task is None:
                # Shuffle victim order to reduce contention
                victim_indices = list(range(self.num_workers))
                random.shuffle(victim_indices)
                
                for idx in victim_indices:
                    if idx == worker_id: continue
                    task = self.queues[idx].steal()
                    if task:
                        break
            
            # 3. Execute or wait
            if task:
                try:
                    func, args, kwargs, result_container = task
                    result = func(*args, **kwargs)
                    result_container.append(result)
                except Exception as e:
                    logger.error(f"WorkStealingPool Error: {e}")
            else:
                # No work anywhere, take a tiny nap to prevent CPU thrashing
                time.sleep(0.001)

    def apply_batch(self, tasks):
        """
        Submits a batch of tasks. 
        Tasks should be [(func, args, kwargs), ...]
        Returns a list that will be populated with results.
        """
        results = []
        # Round-robin initial distribution
        for i, (func, args, kwargs) in enumerate(tasks):
            queue_idx = i % self.num_workers
            self.queues[queue_idx].push_task((func, args, kwargs, results))
        
        # Wait for completion (simple spin-wait for the proof of concept)
        total = len(tasks)
        while len(results) < total:
            time.sleep(0.002)
            
        return results

    def shutdown(self):
        self._shutdown = True
        for t in self.threads:
            t.join(timeout=0.1)
