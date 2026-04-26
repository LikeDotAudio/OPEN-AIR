# oaTests/Methods/FlameGraph/flame_capture.py
# Author: Anthony Peter Kuzub
# Version: 20260406.0040.1
#
# Description: Low-level Multi-threaded Profiling Hooks.
# Surgical fixes for NameError and multi-thread capture.

import cProfile
import gc
import pstats
import sys
import threading

from oaLogging.Entry import TEST_LOGGER


def kill_all_profilers():
    """Safety cleanup: stops any dangling profilers in the environment."""
    sys.setprofile(None)
    count = 0
    for obj in gc.get_objects():
        try:
            if isinstance(obj, cProfile.Profile):
                obj.disable()
                count += 1
        except Exception:
            pass
    if count > 0:
        TEST_LOGGER.trace(f"FlameGraph: Watchdog killed {count} active profiler(s).")

class MultiThreadProfiler:
    """Orchestrates profiling across the main thread and all spawned child threads."""
    def __init__(self):
        self.profilers = []
        self.lock = threading.Lock()
        self.main_profiler = cProfile.Profile()
        self._is_installed = False

    def install(self):
        if self._is_installed:
            return

        kill_all_profilers()

        # Ensure main profiler is enabled
        self.main_profiler.enable()

        if not hasattr(threading.Thread, "_original_run"):
            threading.Thread._original_run = threading.Thread.run

        original_run = threading.Thread._original_run
        outer_self = self

        def patched_run(self_thread):
            # Clear any inherited profilers in this new thread
            kill_all_profilers()

            p = cProfile.Profile()
            try:
                p.enable()
                with outer_self.lock:
                    outer_self.profilers.append(p)
                try:
                    original_run(self_thread)
                finally:
                    p.disable()
            except ValueError as e:
                TEST_LOGGER.warning(f"FlameGraph: Profiler enable failed: {e}")
                # Fallback if another profiler is active (e.g. nested calls)
                original_run(self_thread)

        threading.Thread.run = patched_run
        self._is_installed = True

    def stop(self):
        if not self._is_installed:
            return
        self.main_profiler.disable()
        if hasattr(threading.Thread, "_original_run"):
            threading.Thread.run = threading.Thread._original_run
        self._is_installed = False

    def get_stats(self):
        self.main_profiler.disable()

        # Initialize with main thread stats
        try:
            combined_stats = pstats.Stats(self.main_profiler)
        except TypeError:
            # Fallback to empty stats if main_profiler is somehow still empty
            # We use an empty Profile that has been toggled to ensure it's not "empty"
            empty_p = cProfile.Profile()
            empty_p.enable()
            empty_p.disable()
            combined_stats = pstats.Stats(empty_p)

        with self.lock:
            for p in self.profilers:
                p.disable()
                try:
                    combined_stats.add(pstats.Stats(p))
                except (TypeError, ValueError, RuntimeError):
                    continue
        return combined_stats
