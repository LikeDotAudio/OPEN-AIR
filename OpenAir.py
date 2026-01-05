import sys
import os
import pathlib

# Get the directory of the current script (OpenAir.py)
current_script_dir = pathlib.Path(__file__).resolve().parent

# Add the project root (which is current_script_dir in this case) to sys.path
if str(current_script_dir) not in sys.path:
    sys.path.insert(0, str(current_script_dir   ))

import threading # Added for the threading solution
import inspect
import tkinter as tk
import importlib   

# --- Custom Module Imports (Config MUST be read first) ---
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance and ensure config is read

# --- Core Application Imports ---
from managers.dependancy import dependancy_checker


# Other essential modules
from workers.splash_screen.splash_screen import SplashScreen
from workers.Worker_Launcher import WorkerLauncher
import display.gui_display
from workers.logger.logger import  debug_logger

import workers.setup.path_initializer as path_initializer
import workers.logger.logger_config as logger_config
import managers.configini.console_encoder as console_encoder
import workers.setup.debug_cleaner as debug_cleaner
from workers.setup.application_initializer import initialize_app
from workers.logger.log_utils import _get_log_args
from managers.manager_launcher import launch_managers

current_version = "20251226.000000.1"

def _reveal_main_window(root, splash):
    debug_logger(message="DEBUG: Entering _reveal_main_window.", **_get_log_args())
    if app_constants.ENABLE_DEBUG_SCREEN:
        debug_logger(message="DEBUG: Revealing main window...", **_get_log_args())
    debug_logger(message="DEBUG: Calling root.deiconify().", **_get_log_args())
    root.deiconify() # Ensure main window is visible
    debug_logger(message="DEBUG: Calling splash.hide().", **_get_log_args())
    splash.hide()    # Dismiss the splash screen
    debug_logger(message="DEBUG: _reveal_main_window completed.", **_get_log_args())

def _reveal_main_window(root, splash):
    debug_logger(message="DEBUG: Entering _reveal_main_window.", **_get_log_args())
    if app_constants.ENABLE_DEBUG_SCREEN:
        debug_logger(message="DEBUG: Revealing main window...", **_get_log_args())
    debug_logger(message="DEBUG: Calling root.deiconify().", **_get_log_args())
    root.deiconify() # Ensure main window is visible
    debug_logger(message="DEBUG: Calling splash.hide().", **_get_log_args())
    splash.hide()    # Dismiss the splash screen
    debug_logger(message="DEBUG: _reveal_main_window completed.", **_get_log_args())

def _initialize_application(root, splash):
    debug_logger(message="DEBUG: Entering _initialize_application (background thread).", **_get_log_args())
    try:
        # MQTT Connection Manager
        from workers.mqtt.mqtt_connection_manager import MqttConnectionManager
        mqtt_connection_manager = MqttConnectionManager()
        # State Cache Manager
        from workers.State_Cache.state_cache_manager import StateCacheManager
        state_cache_manager = StateCacheManager(mqtt_connection_manager) # Pass mqtt_connection_manager     
        # Launch managers
        managers = launch_managers(app=None, splash=splash, root=root, state_cache_manager=state_cache_manager, mqtt_connection_manager=mqtt_connection_manager) # Pass mqtt_connection_manager
        if managers is None:
            debug_logger(message="❌ Manager launch failed. Exiting application.", **_get_log_args())
            # Since we are in a thread, cannot sys.exit directly, must schedule main thread shutdown
            root.after(0, root.quit) # Schedule main thread to quit
            return
        # Debug: Inspect managers dictionary
        debug_logger(message=f"✅ Managers launched: {managers}", **_get_log_args())

        # --- WAIT FOR INITIAL SCAN ---
        # The splash screen will remain visible until the initial device discovery is complete.
        visa_fleet_manager = managers.get("visa_fleet_manager")
        if visa_fleet_manager:
            # Wait for the scan to finish, with a timeout of 60 seconds.
            visa_fleet_manager.wait_for_initial_scan(timeout=60)
        else:
            debug_logger(message="⚠️ Visa_fleet_manager not found in managers dict, cannot wait for scan.", **_get_log_args())

        # Now that the scan is complete, proceed with building the main display.
        app = action_open_display(root, splash,
                                  mqtt_connection_manager=managers["mqtt_connection_manager"],
                                  subscriber_router=managers["subscriber_router"],
                                  state_cache_manager=state_cache_manager)
        def on_closing():
            """Gracefully shuts down the application."""
            if app:
                app.shutdown()
            root.destroy()
        root.protocol("WM_DELETE_WINDOW", on_closing)
        # Schedule closing splash and revealing main window on the main Tkinter thread
        root.after(0, _reveal_main_window, root, splash)
    except Exception as e:
        debug_logger(message=f"❌ CRITICAL ERROR in _initialize_application (background thread): {e}", **_get_log_args())
        import traceback
        traceback.print_exc()
        root.after(0, root.quit) # Schedule main thread to quit on error

def action_open_display(root, splash, mqtt_connection_manager, subscriber_router, state_cache_manager):
    """
    Builds and displays the main application window, ensuring the splash
    screen remains responsive by updating the event loop between heavy steps.
    """
    current_function_name = inspect.currentframe().f_code.co_name
    debug_logger(message=f"▶️ Entering {current_function_name}", **_get_log_args())

    try:
        # Each step is followed by root.update() to process events and keep the splash screen alive.
        root.update()
        ApplicationModule = importlib.import_module("display.gui_display")
        Application = getattr(ApplicationModule, "Application")     
        debug_logger(message=f"⚙️ Preparing to instantiate Application with: mqtt_connection_manager={mqtt_connection_manager}, subscriber_router={subscriber_router}, state_mirror_engine={state_cache_manager.state_mirror_engine}", **_get_log_args())
        # This is the primary long-running GUI task.
        # We pass the root window to the Application so it can call update() internally.
        app = Application(parent=root, root=root,
                          mqtt_connection_manager=mqtt_connection_manager,
                          subscriber_router=subscriber_router,
                          state_mirror_engine=state_cache_manager.state_mirror_engine)
        app.pack(fill=tk.BOTH, expand=True)
        root.update()        
        worker_launcher = WorkerLauncher(
            splash_screen=splash,
            console_print_func=app.print_to_console,
        )
        worker_launcher.launch_all_workers()
        root.update()
        debug_logger(message="DEBUG: Calling _reveal_main_window.", **_get_log_args())
        _reveal_main_window(root, splash)
        debug_logger(message="DEBUG: _reveal_main_window returned.", **_get_log_args())       
        return app



    except Exception as e:
        debug_logger(message=f"❌ CRITICAL ERROR in {current_function_name}: {e}", **_get_log_args())
        import traceback
        traceback.print_exc()
        return None

def main():
    """The main execution function for the application."""
    GLOBAL_PROJECT_ROOT = None
    data_dir = None

    import sys 
    from workers.setup.path_initializer import initialize_paths
    from workers.logger.logger import set_log_directory
    from workers.setup.debug_cleaner import clear_debug_directory
    from managers.configini.console_encoder import configure_console_encoding
    import pathlib
    import workers.watchdog.watchdog as watchdog # Import watchdog

    GLOBAL_PROJECT_ROOT, data_dir = initialize_paths()
    log_dir = pathlib.Path(data_dir) / "debug"
    # clear_debug_directory(data_dir)
    set_log_directory(log_dir)
    configure_console_encoding()
    # START THE WATCHDOG
    watchdog.start_heartbeat(debug_logger, app_constants)    
    # Now that the logger is safe, we can proceed with the rest of the setup.
    if not initialize_app():
        debug_logger(message="❌ Critical initialization failed. Application will now exit.", **_get_log_args())
        sys.exit(1)
    # Perform dependency check after initial setup
    def conditional_console_print(message):
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(message=message, **_get_log_args())
    dependancy_checker.run_interactive_pre_check(conditional_console_print, debug_logger, app_constants)
    # --- GUI setup starts here, after core initialization is complete ---
    root = tk.Tk()
    root.configure(bg="#2b2b2b")
    root.title("OPEN-AIR 2")
    root.geometry("1600x1200")
    root.withdraw() # Hide the main window initially
    # Instantiate the splash screen
    splash = SplashScreen(root, app_constants.CURRENT_VERSION, app_constants.global_settings['debug_enabled'], debug_logger, debug_logger)
    root.splash_window = splash.splash_window # Strong reference
    # Create and start a new thread for application initialization
    app_init_thread = threading.Thread(target=_initialize_application, args=(root, splash))
    app_init_thread.start()
    debug_logger(message="DEBUG: Entering root.mainloop().", **_get_log_args())
    # Finally, enter the main event loop. This will manage the splash screen and then the main app.
    root.mainloop()

if __name__ == "__main__":
    main()