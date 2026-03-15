# workers/Worker_Launcher.py
#
# Primary Purpose:
# Orchestrate the initialization, configuration, and execution of all background
# worker processes for the OPEN-AIR application. This file acts as the central
# authority for the worker lifecycle, ensuring that all necessary subsystems
# are instantiated and operational before the main application loop takes over.
#
# Responsibilities:
# - Manage the sequence of worker initialization to handle dependencies.
# - Provide visual feedback to the user via the splash screen during startup.
# - Handle and log errors that occur during the critical worker launch phase.
# - Maintain a consistent execution environment for all background tasks.
#
# Constraints:
# - Requires a valid 'config.ini' file to be present and readable.
# - Execution assumes an active event loop for logging and UI updates.
# - Assumes a thread-safe environment for initial worker instantiation.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your
# specific application can be negotiated. There is no charge to use, modify,
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1

import os
import inspect

# --- Standard Debug Logging Setup ---
# LOCAL_DEBUG: Toggles verbose logging for internal development diagnostics.
LOCAL_DEBUG = True
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

# Retrieve the global configuration singleton to access application constants.
app_constants = Config.get_instance()

# --- Global Scope Variables ---
# Metadata used for versioning and identifying the execution context.
current_date = 20251215
current_time = 120000
current_iteration = 2

current_version = f"{current_date}.{current_time}.{current_iteration}"
current_version_hash = current_date * current_time * current_iteration
current_file = f"{os.path.basename(__file__)}"


class WorkerLauncher:
    """
    Manages the initialization and launching of all application workers.
    
    This class serves as the supervisor for the worker subsystem, coordinating
    the startup of various background processes and providing a unified
    interface for the application's boot sequence.
    """

    def __init__(self, splash_screen, console_print_func):
        """
        Initializes the WorkerLauncher supervisor.

        Inputs:
            splash_screen (SplashScreen): An object conforming to the
                SplashScreen interface, used for providing visual progress
                updates to the user. Must not be NULL.
            console_print_func (function): A callback function used to route
                messages to the application's internal console/log display.
                Must accept a single string argument.

        Outputs:
            None.

        Side Effects:
            - Assigns the provided objects to instance variables.
            - Captures the class name for use in internal logging.
        
        Thread Safety:
            Should be instantiated on the main application thread to ensure
            proper UI object synchronization.
        """
        # Adhering to 'No Magic Numbers' principle. We store these references
        # early to ensure they are available for the entire launch sequence.
        self.splash = splash_screen
        self._print_to_gui_console = console_print_func
        self.current_class_name = self.__class__.__name__

    def launch_all_workers(self):
        """
        Initializes and starts all registered worker processes.

        Lead with action: Orchestrates the instantiation and startup of all
        background workers required for the application's operation. This
        is a blocking call that completes once the startup sequence finishes.

        Inputs:
            None.

        Outputs:
            bool: Returns True if the entire sequence completed without
                uncaught exceptions; returns False if a critical failure
                occurred during initialization.

        Side Effects:
            - Modifies global state by instantiating worker objects.
            - Updates the splash screen status messages.
            - Writes detailed diagnostics to the loguru-managed log stream.

        Thread Safety:
            Executes on the calling thread. Individual workers may spawn their
            own threads or processes upon initialization.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if LOCAL_DEBUG:
            logger.debug(f"🟢️️️🟢 Eureka! We are kicking off the worker "
                         f"engines from '{current_function_name}'!")

        try:
            # The launch sequence is designed to be extensible. New workers
            # should be instantiated and registered here.
            
            # --- Status updates handled by root.update() in main.py ---
            # self.splash.set_status("Initializing workers...")

            # Implementation Note:
            # ActivePeakPublisher is the primary data distribution worker.
            # Its initialization triggers the data ingestion pipeline.
            ## active_peak_publisher = ActivePeakPublisher()
            
            # self.splash.set_status("Active Peak Publisher initialized.")
            if LOCAL_DEBUG:
                logger.debug("🟢️️️🔵 Worker 'ActivePeakPublisher' initialized. "
                             "The lab is buzzing with activity!")

            # --- Celebration of Success ---
            if LOCAL_DEBUG:
                logger.success("✅ All workers have been successfully "
                               "conjured and set to their tasks!")
            return True

        except Exception as e:
            # Critical error handling: If any part of the worker launch fails,
            # we log the traceback and return False to allow the caller to
            # decide whether to proceed or halt the application.
            if LOCAL_DEBUG:
                logger.exception(f"❌ A dreadful error occurred in "
                                 f"'{current_function_name}'")
                logger.exception(f"❌ The worker initialization has gone "
                                 f"haywire in '{current_function_name}'! "
                                 f"The error: {e}")
            return False
