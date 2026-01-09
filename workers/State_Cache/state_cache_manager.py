# State_Cache/state_cache_manager.py
#
# Manages the overall state cache system, orchestrating I/O, traffic control, and GUI restoration.
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

import inspect
from typing import Dict, Any

from . import cache_io_handler
from . import cache_traffic_controller
from . import gui_state_restorer
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251230.230400.1"
current_version_hash = 20251230 * 230400 * 1


class StateCacheManager:
    """
    The public API for the state cache system.
    """

    # Initializes the StateCacheManager.
    # This constructor sets up the manager with references to the MQTT connection
    # and state mirror engines, and initializes the internal cache dictionary.
    # Inputs:
    #     mqtt_connection_manager (Any): An instance of the MQTT connection manager.
    #     state_mirror_engine (Any, optional): An instance of the state mirror engine.
    # Outputs:
    #     None.
    def __init__(self, mqtt_connection_manager: Any, state_mirror_engine: Any = None):
        """
        Spools up the IO Handler and Traffic Controller.
        """
        self.mqtt_connection_manager = mqtt_connection_manager
        self.state_mirror_engine = state_mirror_engine
        self.cache = {}
        self.subscriber_router = None
        debug_logger(
            message="🚀 Great Scott! The State Cache Manager is online! We're ready to manipulate the timeline!",
            **_get_log_args(),
        )

    # Subscribes to all MQTT topics under the "OPEN-AIR/#" root to capture all application state.
    # This method ensures that the StateCacheManager receives all relevant MQTT messages,
    # allowing it to maintain a comprehensive and up-to-date cache of the application's state.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def subscribe_to_all_topics(self):
        """
        Subscribes to all topics under the OPEN-AIR root to capture all state.
        """
        topic = "OPEN-AIR/#"
        self.mqtt_connection_manager.client.subscribe(topic)
        debug_logger(
            message=f"📡 StateCacheManager subscribing to topic: {topic}",
            **_get_log_args(),
        )

    # Initializes the application state by loading the cache from disk and restoring the GUI.
    # This function orchestrates the loading of cached data from `device_state_snapshot.json`
    # and, if data is present, uses the GUI state restorer to bring the GUI to its last known state.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def initialize_state(self) -> None:
        """
        Calls IO load -> calls Restorer.
        """
        debug_logger(
            message="🧐 Initializing the timeline... let's see what the past holds.",
            **_get_log_args(),
        )
        self.cache = cache_io_handler.load_cache()
        if self.cache:
            debug_logger(
                message="📖 The Almanac has entries! Engaging the Time Circuits!",
                **_get_log_args(),
            )
            gui_state_restorer.restore_timeline(self.cache, self.state_mirror_engine)
        else:
            debug_logger(
                message="🐣 The Almanac is empty. Starting with a fresh timeline.",
                **_get_log_args(),
            )

    # Handles incoming MQTT messages, processes them, updates the cache, and forwards them.
    # This method acts as a central handler for all incoming MQTT traffic. It uses
    # the cache traffic controller to determine if an update is necessary, updates
    # the internal cache, saves the cache to disk, and then forwards the message
    # to the subscriber router.
    # Inputs:
    #     client: The Paho MQTT client instance.
    #     userdata: User-defined data passed to the callback.
    #     msg: The Paho MQTT message object.
    # Outputs:
    #     None.
    def handle_incoming_mqtt(self, client, userdata, msg) -> None:
        """
        Calls Traffic Controller -> Calls IO Save (if changed) -> Calls router.
        """
        topic = msg.topic
        payload = msg.payload
        debug_logger(message=f"🌀 Topic: {topic}", **_get_log_args())

        should_process, new_payload = cache_traffic_controller.process_traffic(
            topic, payload, self.cache
        )

        if should_process:
            debug_logger(
                message="🏋️ This is heavy! The timeline has been altered. Recording the new event.",
                **_get_log_args(),
            )
            self.cache[topic] = new_payload
            cache_io_handler.save_cache(self.cache)
        else:
            debug_logger(
                message="👯 The event is a duplicate. No alteration to the timeline needed.",
                **_get_log_args(),
            )

        if self.subscriber_router:
            debug_logger(
                message="⏩ Forwarding the temporal flux to the main timeline...",
                **_get_log_args(),
            )
            self.subscriber_router._on_message(client, userdata, msg)
        else:
            debug_logger(
                message="🤷 Nowhere to route the temporal flux! The subscriber router is missing!",
                **_get_log_args(),
            )