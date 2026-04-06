# Core/bootstrap_sequence.py
# Author: Anthony Peter Kuzub
# Version: 20260322.Modular.1
#
# Description: Non-blocking initialization sequence for UI and Comms.

import tkinter as tk
import traceback
import time
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
        self.start_time = time.time()
        self.MIN_SPLASH_TIME = 10.0 # Minimum splash screen duration in seconds

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
            # INCREASED DELAY: Give X11 200ms to stabilize and process destruction events
            # of any transient windows before the heavy GUI build begins.
            self.root.after(200, lambda: self._launch_app(
                mqtt_conn=services["mqtt_conn"], 
                sub_router=services["sub_router"], 
                mirror_engine=services["mirror_engine"], 
                state_cache=services["state_cache"]
            ))

        except Exception:
            logger.exception("🖥️🎨 [UI] Bootstrap Failure")
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
        """Starts conditional services like OSC, SNMP, MIDI, and REST if configured."""
        service_map = {
            "osc_manager": "OSC",
            "snmp_manager": "SNMP",
            "midi_manager": "MIDI",
            "rest_manager": "REST API"
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
            from oaGuiFramework.Entry import Application
            from .ui_window import UIWindowManager

            # ⚡ SANITIZATION: Destroy the splash screen BEFORE building the application 
            # GUI to prevent X11 display handle race conditions (Matplotlib vs. Splash).
            self.splash.hide()
            self.root.update_idletasks()

            with mirror_engine.suspend_bindings():
                def _on_ignition_complete():
                    # Calculate remaining time to fulfill the 10-second minimum
                    elapsed_time = time.time() - self.start_time
                    remaining_time = max(0, self.MIN_SPLASH_TIME - elapsed_time)
                    
                    def _finish():
                        self.splash.set_status(message="Ignition Complete!")
                        UIWindowManager.reveal_main_window(self.root, self.splash, self.app_constants.global_settings["debug_enabled"])
                        mirror_engine._schedule_queue_processing()
                    
                    # Split the remaining time into 3 "Ignition" phases for visual feedback
                    phase_duration = remaining_time / 3.0
                    
                    def _phase_2():
                        self.splash.set_status(message="Ignition Phase 2: Building systems...")
                        self.root.after(int(phase_duration * 1000), _phase_3)

                    def _phase_3():
                        self.splash.set_status(message="Ignition Phase 3: Finalizing...")
                        self.root.after(int(phase_duration * 1000), _finish)

                    self.splash.set_status(message="Ignition Phase 1: Warming up...")
                    self.root.after(int(phase_duration * 1000), _phase_2)

                try:
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
                except tk.TclError as e:
                    logger.error(f"🖥️🎨 [UI] TclError during Application build: {e}")
                    # Attempt a final rescue deiconify
                    self.root.deiconify()
                
                # Register main app back to services
                self.services["app"] = app
                self.root.update_idletasks()
                
        except Exception:
            logger.exception("🖥️🎨 [UI] App Launch Failure")
            self.root.after(0, self.shutdown_coordinator.on_closing)
