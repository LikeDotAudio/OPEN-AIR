# workers/watchdog/watchdog.py
#
# Primary Purpose:
# This module implements a robust watchdog timer designed to monitor the health
# and responsiveness of the application's main GUI thread. It provides an
# automated "panic" mechanism that triggers a hard process exit if the main
# thread becomes unresponsive (hangs) for a predefined duration.
#
# Responsibilities:
# - Track the last 'heartbeat' (kick) received from the main thread.
# - Execute a background monitoring loop to verify thread activity.
# - Capture and report the main thread's stack trace upon failure.
# - Execute registered panic callbacks (e.g., emergency logging, state dumping).
# - Forcefully terminate the application using '_os._exit(1)' to prevent 
#   cascading failures in distributed systems.
#
# Constraints:
# - Requires 'threading' and 'sys' for thread enumeration and frame access.
# - Assumes 'kick_watchdog()' is called regularly (e.g., from the UI loop).
# - Hard-coded 120-second timeout threshold; must be tuned for hardware.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260125.WatchdogOverhaul.1

import threading
import time
import sys
import os as _os
import traceback

# --- Standard Debug Logging Setup ---
# LOCAL_DEBUG: Toggles verbose watchdog state reporting to the terminal.
LOCAL_DEBUG = True
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config

# Retrieve the global configuration singleton.
app_constants = Config.get_instance()

# --- Global Watchdog State ---
# WATCHDOG_RUNNING: Controls the execution of the background monitoring loop.
WATCHDOG_RUNNING = True
# LAST_HEARTBEAT_TIME: Unix timestamp of the most recent 'kick'.
LAST_HEARTBEAT_TIME = time.time()
# TIMEOUT_THRESHOLD: Duration (seconds) of silence before triggering a panic.
TIMEOUT_THRESHOLD = 120.0
# PANIC_CALLBACKS: List of functions to execute immediately before termination.
PANIC_CALLBACKS = []

def _get_main_thread_stack():
    """
    Retrieves the current execution stack of the application's main thread.

    Lead with action: Iterates through all active threads to find the main
    thread, then extracts its current frame to format a readable stack trace.

    Inputs:
        None.

    Outputs:
        str: A formatted stack trace of the main thread if successful; 
             otherwise, an error message string.

    Side Effects:
        - Accesses 'sys._current_frames()', which may have slight performance
          implications if called at high frequency (not an issue for panics).
    """
    for thread in threading.enumerate():
        if thread is threading.main_thread():
            frame = sys._current_frames().get(thread.ident)
            if frame:
                return "".join(traceback.format_stack(frame))
    return "Could not retrieve main thread stack."

def kick_watchdog():
    """
    Signals that the main thread is still active and responsive.

    Lead with action: Updates the global 'LAST_HEARTBEAT_TIME' with the current
    monotonic time. 

    Inputs:
        None.

    Outputs:
        None.

    Side Effects:
        - Updates the shared 'LAST_HEARTBEAT_TIME' global variable.

    Note:
        This function MUST be called from the primary event loop (e.g., within
        a Tkinter '.after()' callback or a main 'while' loop).
    """
    global LAST_HEARTBEAT_TIME
    LAST_HEARTBEAT_TIME = time.time()

def start_heartbeat(app_constants_instance=None):
    """
    Initializes and starts the background monitoring thread.

    Inputs:
        app_constants_instance (Config, optional): Instance of the config
            reader. Defaults to the global singleton if NULL.

    Outputs:
        None.

    Side Effects:
        - Resets the watchdog state.
        - Spawns a new daemon thread running '_heartbeat_loop'.
    """
    global WATCHDOG_RUNNING, LAST_HEARTBEAT_TIME
    WATCHDOG_RUNNING = True
    LAST_HEARTBEAT_TIME = time.time()

    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(app_constants_instance,),
        daemon=True,
    )
    thread.start()
    
    if LOCAL_DEBUG:
        logger.debug(
            f"🐕⏳🔋 [WATCHDOG] Started (Timeout: {TIMEOUT_THRESHOLD}s)"
        )

def stop_heartbeat():
    """
    Signals the watchdog monitoring thread to terminate gracefully.
    """
    global WATCHDOG_RUNNING
    WATCHDOG_RUNNING = False

def register_panic_callback(callback):
    """
    Adds a function to the emergency execution list.

    Inputs:
        callback (function): A callable that takes no arguments. This function
            will be executed if the watchdog triggers a panic.
    """
    if callback not in PANIC_CALLBACKS:
        PANIC_CALLBACKS.append(callback)

def _heartbeat_loop(app_constants_instance):
    """
    Background monitoring loop for the watchdog subsystem.

    Lead with action: Periodically checks the time elapsed since the last
    heartbeat. If the elapsed time exceeds the threshold, it initiates
    a system panic.

    Inputs:
        app_constants_instance (Config): Configuration context for logging.

    Outputs:
        None.

    Side Effects:
        - Writes diagnostics to 'sys.stdout' and 'sys.stderr'.
        - Triggers a hard exit of the entire process group via '_os._exit(1)'.
    
    Implementation Note:
        The loop sleeps for 10 seconds between checks. This provides a balance
        between monitoring precision and CPU overhead.
    """
    counter = 0
    while WATCHDOG_RUNNING:
        time.sleep(10.0)
        counter += 1
        
        current_time = time.time()
        elapsed = current_time - LAST_HEARTBEAT_TIME

        # CRITICAL FAILURE DETECTED:
        # If the main thread has not checked in within the timeout threshold,
        # we assume a deadlock or a heavy blocking operation has occurred.
        if elapsed > TIMEOUT_THRESHOLD:
            logger.error(
                f"🐕⏳❌ [ERROR] WATCHDOG CRITICAL: Main thread frozen "
                f"for {elapsed:.1f}s!"
            )
            sys.stdout.write(f"\n🔥 [WATCHDOG] CRITICAL: Main thread frozen "
                             f"for {elapsed:.1f}s!\n")
            sys.stdout.write("💀 [WATCHDOG] Current Stack Trace:\n")
            sys.stdout.write("----------------------------------------\n")
            try:
                stack = _get_main_thread_stack()
                sys.stdout.write(stack)
            except Exception as e:
                logger.error(
                    f"🐕⏳❌ [ERROR] Watchdog: Error retrieving stack: {e}"
                )
                sys.stdout.write(f"Error retrieving stack: {e}")
            sys.stdout.write("\n----------------------------------------\n")
            
            # Execute Panic Callbacks:
            # This is the final opportunity for the system to perform 
            # cleanup or emergency telemetry (e.g., flamegraph generation).
            if PANIC_CALLBACKS:
                logger.error(
                    f"🐕⏳🚑 [ERROR] WATCHDOG: Executing "
                    f"{len(PANIC_CALLBACKS)} panic callbacks..."
                )
                sys.stdout.write(f"🚑 [WATCHDOG] Executing "
                                 f"{len(PANIC_CALLBACKS)} callbacks...\n")
                sys.stdout.flush()
                for cb in PANIC_CALLBACKS:
                    try:
                        cb()
                    except Exception as e:
                        logger.error(
                            f"🐕⏳❌ [ERROR] Watchdog: Callback failed: {e}"
                        )
                        sys.stdout.write(f"❌ [WATCHDOG] Callback failed: {e}\n")
            
            logger.critical("💀🐕🛑 [CRITICAL] Watchdog: Forcefully terminating.")
            sys.stdout.write("💀 [WATCHDOG] Forcefully terminating...\n")
            sys.stdout.flush()
            
            # Use _os._exit(1) to bypass Python's standard 'sys.exit()' 
            # cleanup handlers, which might themselves be deadlocked.
            _os._exit(1)

        # Health Grading:
        # Provide graduated warnings before reaching the hard timeout.
        status_text = "Healthy"
        if elapsed > TIMEOUT_THRESHOLD * 0.9:
            status_text = "FAILING!"
            logger.warning(f"🐕⏳⚠️ [WARNING] Watchdog: System {status_text} ({elapsed:.1f}s)")
        elif elapsed > TIMEOUT_THRESHOLD * 0.8:
            status_text = "In Trouble"
            logger.warning(f"🐕⏳⚠️ [WARNING] Watchdog: System {status_text} ({elapsed:.1f}s)")
        elif elapsed > TIMEOUT_THRESHOLD * 0.5:
            status_text = "Unresponsive"
            logger.warning(f"🐕⏳⚠️ [WARNING] Watchdog: System {status_text} ({elapsed:.1f}s)")

        if LOCAL_DEBUG:
            sys.stdout.write(f"\r🐕 [WATCHDOG] Tick {counter}: System "
                             f"{status_text} (Last Kick: {elapsed:.1f}s ago)")
            sys.stdout.flush()

        # Log heartbeat status occasionally to the file logger.
        if counter % 5 == 0:
            try:
                if LOCAL_DEBUG:
                    logger.debug(f"🐕💓🐕 [WATCHDOG] Heartbeat {counter}")
            except:
                pass
