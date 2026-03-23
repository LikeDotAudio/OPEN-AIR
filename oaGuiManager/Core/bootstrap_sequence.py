# Core/bootstrap_sequence.py
# Author: Anthony Peter Kuzub
# Version: 20260322.Modular.1
#
# Description: Non-blocking initialization sequence for UI and Comms.

import tkinter as tk
import traceback
from loguru import logger

class AsyncBootstrapEngine:
    """
    Manages the non-blocking initialization sequence for UI and Comms.
    Consumes services provided by the Composition Root.
    """

    def __init__(self, root, splash, services, app_constants, shutdown_coordinator):
        self.root = root
        self.splash = splash
        self.services = services
        self.app_constants = app_constants
        self.shutdown_coordinator = shutdown_coordinator

    def run(self):
        """
        Executes the async startup sequence using injected services.
        """
        try:
            services = self.services
            
            # Phase 1: Communication
            self._connect_communication_services(
                mqtt_conn=services["mqtt_conn"], 
                sub_router=services["sub_router"], 
                state_cache=services["state_cache"]
            )

            # Phase 2: Protocols
            self._start_protocol_services(protocol_router=services["protocol_router"])

            # Phase 3: External
            self._start_optional_services()

            # Phase 4: Control Links
            self._setup_control_links(
                sub_router=services["sub_router"], 
                splinker=services["splinker_manager"]
            )

            # Phase 5: Launch
            self.root.after(1, lambda: self._launch_app(
                mqtt_conn=services["mqtt_conn"], 
                sub_router=services["sub_router"], 
                mirror_engine=services["mirror_engine"], 
                state_cache=services["state_cache"]
            ))

        except Exception:
            logger.exception(f"🖥️🎨 [UI] Bootstrap Failure:{traceback.format_exc()}")
            self.root.after(0, self.shutdown_coordinator.on_closing)

    def _connect_communication_services(self, mqtt_conn, sub_router, state_cache):
        """Initializes the connection to the MQTT broker and sets up state subscriptions."""
        self.splash.set_status(message="Connecting to Broker...")
        mqtt_conn.connect_to_broker(
            on_message_callback=state_cache.handle_incoming_mqtt, 
            subscriber_router=sub_router
        )
        state_cache.subscribe_to_all_topics()

    def _start_protocol_services(self, protocol_router):
        """Starts the main protocol routing services."""
        self.splash.set_status(message="Starting Protocol Services...")
        protocol_router.start()

    def _start_optional_services(self):
        """Starts conditional services like OSC, SNMP, and MIDI if configured."""
        service_map = {
            "osc_manager": "OSC",
            "snmp_manager": "SNMP",
            "midi_manager": "MIDI"
        }
        
        for key, display_name in service_map.items():
            service = self.services.get(key)
            if service:
                self.splash.set_status(message=f"Starting {display_name}...")
                service.start()

    def _setup_control_links(self, sub_router, splinker):
        """Sets up specialized MQTT control topics for internal systems like Splinker."""
        def splinker_mqtt_wrapper(msg): 
            splinker.handle_mqtt_command(topic=msg.topic, payload=msg.payload)
        
        sub_router.subscribe_to_topic(
            topic_filter="OPEN-AIR/System/Control/Splinker/#", 
            callback_func=splinker_mqtt_wrapper
        )

    def _launch_app(self, mqtt_conn, sub_router, mirror_engine, state_cache):
        """
        Final phase: Build the Workspace and reveal.
        """
        try:
            self.splash.set_status(message="Building Workspace...")
            from oaGuiBuildShell.Entry import Application
            from .ui_window import UIWindowManager

            with mirror_engine.suspend_bindings():
                def _on_ignition_complete():
                    self.splash.set_status(message="Ignition Complete!")
                    def _finish():
                        UIWindowManager.reveal_main_window(self.root, self.splash, self.app_constants.global_settings["debug_enabled"])
                        mirror_engine._schedule_queue_processing()
                    self.root.after(1, _finish)

                app = Application(
                    parent=self.root, 
                    root=self.root, 
                    mqtt_connection_manager=mqtt_conn, 
                    subscriber_router=sub_router, 
                    state_mirror_engine=mirror_engine, 
                    state_cache_manager=state_cache, 
                    osc_manager=self.services.get("osc_manager"),
                    snmp_manager=self.services.get("snmp_manager"),
                    midi_manager=self.services.get("midi_manager"),
                    on_complete=_on_ignition_complete
                )
                app.pack(fill=tk.BOTH, expand=True)
                
                # Register main app back to services
                self.services["app"] = app
                self.root.update()
                
        except Exception:
            logger.exception(f"🖥️🎨 [UI] App Launch Failure:{traceback.format_exc()}")
            self.shutdown_coordinator.on_closing()
