# workers/utils/watchdog.py
#
# A temporal monitor to detect if the Main Thread has frozen.
#
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1

import threading
import time
import sys
from workers.logger.log_utils import _get_log_args

# Global flag to kill the watchdog when app closes
WATCHDOG_RUNNING = True


def start_heartbeat(debug_logger_func=None, app_constants_instance=None):
    """
    Starts a background thread that prints a heartbeat.
    If the GUI freezes, this thread SHOULD keep printing to the system console (terminal),
    proving that the Python process is alive, but the GUI is stuck.
    """
    global WATCHDOG_RUNNING
    WATCHDOG_RUNNING = True

    thread = threading.Thread(
        target=_heartbeat_loop,
        args=(debug_logger_func, app_constants_instance),
        daemon=True,
    )
    thread.start()
    if (
        app_constants_instance
        and app_constants_instance.global_settings["debug_to_terminal"]
    ):
        print("🐕 Watchdog: Heartbeat thread started.")


def stop_heartbeat():
    global WATCHDOG_RUNNING
    WATCHDOG_RUNNING = False


def _heartbeat_loop(logger_func, app_constants_instance):
    """
    The actual loop running in the background dimension.
    """
    counter = 0
    while WATCHDOG_RUNNING:
        time.sleep(2.0)  # Check every 2 seconds
        counter += 1

        # Message to the System Console (Terminal) - unlikely to freeze
        if (
            app_constants_instance
            and app_constants_instance.global_settings["debug_to_terminal"]
        ):
            sys.stdout.write(f"\r🐕 [Watchdog] Tick {counter}: System Alive.")
            sys.stdout.flush()

        # Message to the GUI/Logger - WILL freeze if GUI is blocked
        if logger_func:
            try:
                # We use a try block because if the GUI is truly dead, this might fail
                logger_func(f"💓 System Heartbeat: {counter}")
            except:
                sys.stdout.write(
                    f"\n❌ [Watchdog] GUI Interaction Failed! Main Thread is BLOCKED!\n"
                )
