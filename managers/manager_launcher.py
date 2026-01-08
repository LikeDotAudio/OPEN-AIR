# managers/manager_launcher.py
#
# This file contains the function to launch and initialize all the application's managers.
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
# Version 20260108.120300.1

import os
import inspect
import threading  # Moved threading import here

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

# --- MQTT and Proxy Imports ---
from workers.mqtt.mqtt_connection_manager import MqttConnectionManager
from workers.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.logic.state_mirror_engine import StateMirrorEngine
from managers.Visa_Fleet_Manager.visa_fleet_manager import (
    VisaFleetManager,
)  # Import VisaFleetManager
from managers.yak.yak_translator import YakTranslator  # Import YakTranslator
from managers.yak.manager_yak_rx import YakRxManager  # Import YakRxManager
from workers.monitoring.fleet_status_monitor import (
    FleetStatusMonitor,
)  # Import FleetStatusMonitor


def launch_managers(app, splash, root, state_cache_manager, mqtt_connection_manager):
    """
    Initializes and launches all the application's managers.

    Args:
        app: The main application object.
        splash (SplashScreen): The splash screen object.
        root (tk.Tk): The root Tkinter window.
        state_cache_manager (StateCacheManager): The state cache manager.
        mqtt_connection_manager (MqttConnectionManager): The MQTT connection manager.

    Returns:
        dict: A dictionary containing all the initialized managers, or None if an error occurs.
    """
    current_function_name = inspect.currentframe().f_code.co_name
    debug_logger(
        message=f"🟢️️️🟢 Entering '{current_function_name}'. Preparing to launch a fleet of managers!",
        **_get_log_args(),
    )
    #   splash.set_status("Initializing managers...")

    try:
        # 1. Initialize MQTT Core Components
        subscriber_router = MqttSubscriberRouter()
        state_mirror_engine = StateMirrorEngine(
            base_topic="OPEN-AIR",
            subscriber_router=subscriber_router,
            root=root,
            state_cache_manager=state_cache_manager,
        )

        # Pass subscriber_router to state_cache_manager and initialize
        state_cache_manager.subscriber_router = subscriber_router
        state_cache_manager.state_mirror_engine = state_mirror_engine
        state_cache_manager.initialize_state()

        # Connect MQTT Client (if not already connected by Application)
        mqtt_connection_manager.connect_to_broker(
            on_message_callback=state_cache_manager.handle_incoming_mqtt,
            subscriber_router=subscriber_router,
        )

        # Subscribe state_cache_manager to all topics
        state_cache_manager.subscribe_to_all_topics()

        # 2. Initialize Visa Fleet Manager
        visa_fleet_manager = VisaFleetManager()
        visa_fleet_manager.start()  # Start the Visa Fleet Manager

        # Automatically trigger a scan after starting the manager in a separate thread
        debug_logger(
            message="💳 Launching initial Visa Fleet scan in a background thread...",
            **_get_log_args(),
        )
        scan_thread = threading.Thread(
            target=visa_fleet_manager.trigger_scan, daemon=True
        )
        scan_thread.start()

        # 3. Initialize Yak Translator
        yak_translator = YakTranslator(
            mqtt_connection_manager=mqtt_connection_manager,
            subscriber_router=subscriber_router,
        )

        # 4. Initialize Yak RX Manager
        yak_rx_manager = YakRxManager(
            mqtt_connection_manager=mqtt_connection_manager,
            subscriber_router=subscriber_router,
            yak_translator=yak_translator,
        )

        # 5. Initialize Fleet Status Monitor
        fleet_status_monitor = FleetStatusMonitor(
            state_mirror_engine=state_mirror_engine, subscriber_router=subscriber_router
        )

        debug_logger(
            message="✅ All core managers have been successfully launched!",
            **_get_log_args(),
        )
        # splash.set_status("Managers initialized.")

        # Consolidate all managers into one dictionary
        all_managers = {
            "mqtt_connection_manager": mqtt_connection_manager,
            "subscriber_router": subscriber_router,
            "state_mirror_engine": state_mirror_engine,
            "visa_fleet_manager": visa_fleet_manager,  # Add VisaFleetManager
            "yak_translator": yak_translator,
            "yak_rx_manager": yak_rx_manager,
            "fleet_status_monitor": fleet_status_monitor,
        }

        # Return instantiated managers for use by the application if needed
        return all_managers

    except Exception as e:
        debug_logger(
            message=f"❌ Critical error during manager launch: {e}", **_get_log_args()
        )
        #     splash.set_status(f"Manager initialization failed: {e}") # Removed error=True
        return None