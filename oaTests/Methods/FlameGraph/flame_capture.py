# FlameGraph/flame_capture.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import cProfile
import pstats
import threading
import gc
import sys

def kill_all_profilers():
    """Safety cleanup: stops any dangling profilers in the environment."""
    sys.setprofile(None)
    count = 0
    for obj in gc.get_objects():
        try:
            if isinstance(obj, cProfile.Profile):
                obj.disable()
                count += 1
        except Exception as e:
            from oaLogging.Entry import logger
            logger.trace(f"FlameGraph: Failed to disable profiler object: {e}")
    if count > 0:
        print(f"? Watchdog: Killed {count} active profiler(s).")

class MultiThreadProfiler:
    """Orchestrates profiling across the main thread and all spawned child threads."""
    def __init__(self):
        self.profilers = []
        self.lock = threading.Lock()
        self.main_profiler = cProfile.Profile()

    def install(self):
        kill_all_profilers()
        original_run = threading.Thread.run
        outer_self = self
        
        def patched_run(self_thread):
            p = cProfile.Profile()
            try:
                p.enable()
                with outer_self.lock:
                    outer_self.profilers.append(p)
                try: original_run(self_thread)
                finally: p.disable()
            except ValueError as e: 
                from oaLogging.Entry import logger
                logger.warning(f"FlameGraph: Profiler enable failed, running thread without profiling: {e}")
                original_run(self_thread)
            
        threading.Thread.run = patched_run
        self.main_profiler.enable()

    def stop(self):
        self.main_profiler.disable()

    def get_stats(self):
        self.main_profiler.disable()
        combined_stats = pstats.Stats(self.main_profiler)
        with self.lock:
            for p in self.profilers:
                p.disable()
                combined_stats.add(pstats.Stats(p))
        return combined_stats
