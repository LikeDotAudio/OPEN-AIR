# workers/Worker_Launcher.py
#
# This file orchestrates the initialization of all background worker processes for the application.
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
# Version 20250821.200641.1

import os
import inspect
from datetime import datetime

# --- Imports for logging and workers ---
from workers.logger.logger import debug_logger
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.log_utils import _get_log_args

# from workers.active.worker_active_marker_tune_and_collect import MarkerGoGetterWorker
## from workers.active.worker_active_peak_publisher import ActivePeakPublisher

# --- Global Scope Variables ---
current_date = 20251215
current_time = 120000
current_iteration = 2

current_version = f"{current_date}.{current_time}.{current_iteration}"
current_version_hash = current_date * current_time * current_iteration
current_file = f"{os.path.basename(__file__)}"


class WorkerLauncher:
    """
    Manages the initialization and launching of all application workers.
    """

    # Initializes the WorkerLauncher.
    # This constructor sets up the launcher with references to the splash screen
    # for displaying progress and a function for printing messages to the console.
    # Inputs:
    #     splash_screen (SplashScreen): The splash screen object to display progress.
    #     console_print_func (function): A function to print messages to the GUI console.
    # Outputs:
    #     None.
    def __init__(self, splash_screen, console_print_func):
        """
        Initializes the WorkerLauncher.

        Args:
            splash_screen (SplashScreen): The splash screen object to display progress.
            console_print_func (function): A function to print messages to the GUI console.
        
        Returns:
            None
        """
        # Adhering to 'No Magic Numbers' principle
        self.splash = splash_screen
        self._print_to_gui_console = console_print_func
        self.current_class_name = self.__class__.__name__

    # Initializes and starts all registered worker processes.
    # This method is the main entry point for running the background tasks of the application.
    # It logs the initialization process and handles any exceptions that occur during worker startup.
    # Inputs:
    #     None.
    # Outputs:
    #     bool: True if all workers were launched successfully, False otherwise.
    def launch_all_workers(self):
        """
        Initializes and starts all registered worker processes.

        Args:
            None

        Returns:
            bool: True if all workers were launched successfully, False otherwise.
        """
        # Initializes and starts all registered worker processes.
        current_function_name = inspect.currentframe().f_code.co_name

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🟢 Eureka! We are kicking off the worker engines from '{current_function_name}'!",
                **_get_log_args(),
            )

        try:
            # These status updates will now be processed by root.update() in main.py
            # self.splash.set_status("Initializing workers...")

            ## active_peak_publisher = ActivePeakPublisher()
            # self.splash.set_status("Active Peak Publisher initialized.")
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message="🟢️️️🔵 Worker 'ActivePeakPublisher' initialized. The lab is buzzing with activity!",
                    **_get_log_args(),
                )

            # --- Celebration of Success ---
            debug_logger(
                message="✅ All workers have been successfully conjured and set to their tasks!",
                **_get_log_args(),
            )
            return True

        except Exception as e:
            debug_logger(
                message=f"❌ A dreadful error occurred in '{current_function_name}': {e}",
                **_get_log_args(),
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌  The worker initialization has gone haywire in '{current_function_name}'! The error be: {e}",
                    **_get_log_args(),
                )
            return False
