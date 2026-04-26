import os as _os
import sys
import threading
import time
import traceback

from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

# --- Native Rust Optimization ---
try:
    from oaRustCore.oa_clock_sync_rs import SystemClock
    _rust_clock = SystemClock()
    HAS_RUST_CLOCK = True
except Exception:
    HAS_RUST_CLOCK = False

def get_precise_time():
    """Returns the current Unix timestamp with the best available precision."""
    if HAS_RUST_CLOCK:
        return _rust_clock.get_micros() / 1_000_000.0
    return time.time()

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
app_constants = Config.get_instance()

# --- Global Watchdog State ---
WATCHDOG_RUNNING = True
LAST_HEARTBEAT_TIME = get_precise_time()
TIMEOUT_THRESHOLD = 120.0
PANIC_CALLBACKS = []

def _get_main_thread_stack():
    """Retrieves the current execution stack of the application's main thread."""
    for thread in threading.enumerate():
        if thread is threading.main_thread():
            frame = sys._current_frames().get(thread.ident)
            if frame:
                return "".join(traceback.format_stack(frame))
    return "Could not retrieve main thread stack."

def kick_watchdog():
    """Signals that the main thread is still active and responsive."""
    global LAST_HEARTBEAT_TIME
    LAST_HEARTBEAT_TIME = get_precise_time()

def start_heartbeat(app_constants_instance=None):
    """Initializes and starts the background monitoring thread."""
    global WATCHDOG_RUNNING, LAST_HEARTBEAT_TIME
    WATCHDOG_RUNNING = True
    LAST_HEARTBEAT_TIME = get_precise_time()

    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(app_constants_instance,),
        daemon=True,
    )
    thread.start()

    if LOCAL_DEBUG:
        logger.debug(f"🐕⏳🔋 [WATCHDOG] Started (Timeout: {TIMEOUT_THRESHOLD}s)")

def stop_heartbeat():
    """Signals the watchdog monitoring thread to terminate gracefully."""
    global WATCHDOG_RUNNING
    WATCHDOG_RUNNING = False

def register_panic_callback(callback):
    """Adds a function to the emergency execution list."""
    if callback not in PANIC_CALLBACKS:
        PANIC_CALLBACKS.append(callback)

def trigger_system_panic(reason="Manual Trigger"):
    """
    Forcefully initiates a system panic and termination.
    """
    logger.critical(f"💀🐕🛑 [CRITICAL] Watchdog: System PANIC triggered! Reason: {reason}")
    sys.stdout.write(f"\n🔥 [WATCHDOG] PANIC: {reason}\n")

    if PANIC_CALLBACKS:
        for cb in PANIC_CALLBACKS:
            try:
                cb()
            except Exception as e:
                logger.error(f"🐕⏳❌ [ERROR] Watchdog: Callback failed: {e}")

    sys.stdout.flush()
    _os._exit(1)

def _heartbeat_loop(app_constants_instance):
    """Background monitoring loop for the watchdog subsystem."""
    counter = 0
    while WATCHDOG_RUNNING:
        time.sleep(10.0)
        counter += 1

        current_time = get_precise_time()
        elapsed = current_time - LAST_HEARTBEAT_TIME

        if elapsed > TIMEOUT_THRESHOLD:
            logger.error(f"🐕⏳❌ [ERROR] WATCHDOG CRITICAL: Main thread frozen for {elapsed:.1f}s!")
            sys.stdout.write(f"\n🔥 [WATCHDOG] CRITICAL: Main thread frozen for {elapsed:.1f}s!\n")
            sys.stdout.write("💀 [WATCHDOG] Current Stack Trace:\n")
            try:
                stack = _get_main_thread_stack()
                sys.stdout.write(stack)
            except Exception as e:
                sys.stdout.write(f"Error retrieving stack: {e}")

            trigger_system_panic("Main thread frozen")

        # Health Grading
        if elapsed > TIMEOUT_THRESHOLD * 0.9:
            logger.warning(f"🐕⏳⚠️ [WARNING] Watchdog: System FAILING! ({elapsed:.1f}s)")
        elif elapsed > TIMEOUT_THRESHOLD * 0.8:
            logger.warning(f"🐕⏳⚠️ [WARNING] Watchdog: System In Trouble ({elapsed:.1f}s)")
        elif elapsed > TIMEOUT_THRESHOLD * 0.5:
            logger.warning(f"🐕⏳⚠️ [WARNING] Watchdog: System Unresponsive ({elapsed:.1f}s)")

class WatchdogManager:
    """
    High-level orchestrator for the watchdog system.
    Follows singleton pattern.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, mqtt_connection_manager=None, subscriber_router=None):
        self.mqtt_connection_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self._running = False

    @classmethod
    def get_instance(cls, mqtt_connection_manager=None, subscriber_router=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(mqtt_connection_manager, subscriber_router)
        return cls._instance

    def start(self):
        """Starts the watchdog monitoring."""
        if not self._running:
            start_heartbeat(app_constants)
            self._running = True
            matrix_log("core", "system", "watchdog", "🚀 Watchdog monitoring active.", "INFO")

    def stop(self):
        """Stops the watchdog monitoring."""
        if self._running:
            stop_heartbeat()
            self._running = False
            matrix_log("core", "system", "watchdog", "⏹️ Watchdog monitoring deactivated.", "INFO")

    def status(self):
        """Returns the status of the watchdog."""
        return "running" if self._running else "stopped"

    def is_alive(self):
        """Checks if the watchdog is alive."""
        return self._running
