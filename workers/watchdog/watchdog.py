# workers/watchdog/watchdog.py
#
# This file implements a watchdog timer to detect if the main GUI thread has frozen.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260108.120800.1

import threading
import time
import sys
from workers.logger.log_utils import _get_log_args

# Global flag to kill the watchdog when app closes
WATCHDOG_RUNNING = True


def start_heartbeat(debug_logger_func=None, app_constants_instance=None):
    """
    Starts a background thread that prints a heartbeat to detect if the main thread has frozen.

    Args:
        debug_logger_func (function, optional): The debug logger function. Defaults to None.
        app_constants_instance (Config, optional): The application constants instance. Defaults to None.
    
    Returns:
        None
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
    """
    Stops the watchdog heartbeat thread.
    
    Args:
        None
        
    Returns:
        None
    """
    global WATCHDOG_RUNNING
    WATCHDOG_RUNNING = False


def _heartbeat_loop(logger_func, app_constants_instance):
    """
    The main loop for the watchdog heartbeat thread.

    Args:
        logger_func (function): The logger function to call.
        app_constants_instance (Config): The application constants instance.
        
    Returns:
        None
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