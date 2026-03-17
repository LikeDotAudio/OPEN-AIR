import tkinter as tk
import traceback
from loguru import logger

# --- Framework Imports ---
from workers.Command_Router.mqtt.mqtt_connection import MqttConnectionManager
from workers.Command_Router.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.Command_Router.State_Cache.state_cache import StateRegistry
from workers.logic.state_mirror_engine import StateMirrorEngine
from workers.Command_Router.protocol_router import ProtocolRouter

# --- External Managers ---
from workers.Command_Router.OSC.osc import OSCManager
from workers.Command_Router.SNMP.snmp import SNMPManager
from workers.Command_Router.MIDI.midi import MidiManager
from workers.Splinker.splinker import ControlBroker

class AsyncBootstrapEngine:
    """Manages the non-blocking initialization sequence for UI and Comms."""

    def __init__(self, root, splash, shared_instances, app_constants, shutdown_coordinator):
        self.root = root
        self.splash = splash
        self.shared_instances = shared_instances
        self.app_constants = app_constants
        self.shutdown_coordinator = shutdown_coordinator

    def run(self):
        try:
            self.app_constants.SCAN_OSC = False

            self.splash.set_status("Initializing Comms...")
            mqtt_conn = MqttConnectionManager()
            self.shared_instances["mqtt_conn"] = mqtt_conn
            sub_router = MqttSubscriberRouter()
            
            self.splash.set_status("Loading State Cache...")
            state_cache = StateRegistry(mqtt_conn)
            state_cache.subscriber_router = sub_router
            self.shared_instances["state_cache"] = state_cache
            
            mirror_engine = StateMirrorEngine(base_topic="OPEN-AIR", subscriber_router=sub_router, root=self.root, state_cache_manager=state_cache)
            state_cache.state_mirror_engine = mirror_engine
            self.shared_instances["mirror_engine"] = mirror_engine
            
            self.splash.set_status("Connecting to Broker...")
            mqtt_conn.connect_to_broker(on_message_callback=state_cache.handle_incoming_mqtt, subscriber_router=sub_router)
            state_cache.subscribe_to_all_topics()

            if self.app_constants.SCAN_OSC:
                self.splash.set_status("Starting OSC...")
                osc = OSCManager(state_cache, mqtt_conn, run_bridge=False)
                osc.start(); self.shared_instances["osc_manager"] = osc

            if self.app_constants.SCAN_SNMP:
                self.splash.set_status("Starting SNMP...")
                snmp = SNMPManager(state_cache, mqtt_conn, run_bridge=False)
                snmp.start(); self.shared_instances["snmp_manager"] = snmp

            self.splash.set_status("Starting MIDI...")
            midi = MidiManager(state_cache, run_bridge=False)
            midi.start(); self.shared_instances["midi_manager"] = midi
            
            self.splash.set_status("Starting Splinker...")
            protocol_router = ProtocolRouter.get_instance()
            self.shared_instances["protocol_router"] = protocol_router
            protocol_router.set_mqtt_manager(mqtt_conn)
            protocol_router.start()
            
            splinker = ControlBroker.get_instance(state_cache, mqtt_conn)
            protocol_router.set_splinker_manager(splinker)
            self.shared_instances["splinker_manager"] = splinker

            def splinker_mqtt_wrapper(msg): splinker.handle_mqtt_command(msg.topic, msg.payload)
            sub_router.subscribe_to_topic("OPEN-AIR/System/Control/Splinker/#", splinker_mqtt_wrapper)
            
            self.root.after(1, lambda: self._launch_app(mqtt_conn, sub_router, mirror_engine, state_cache))
            
        except Exception:
            logger.exception(f"🖥️🎨 [UI] Bootstrap Failure:\n{traceback.format_exc()}")
            self.root.after(0, self.shutdown_coordinator.on_closing)

    def _launch_app(self, mqtt_conn, sub_router, mirror_engine, state_cache):
        try:
            self.splash.set_status("Building Workspace...")
            from managers.Display.builder.gui_display import Application
            from .ui_window import UIWindowManager
            
            with mirror_engine.suspend_bindings():
                def _on_ignition_complete():
                    self.splash.set_status("Ignition Complete!")
                    def _finish():
                        UIWindowManager.reveal_main_window(self.root, self.splash, self.app_constants.global_settings["debug_enabled"])
                        mirror_engine._schedule_queue_processing()
                    self.root.after(1, _finish)

                app = Application(parent=self.root, root=self.root, mqtt_connection_manager=mqtt_conn, subscriber_router=sub_router, state_mirror_engine=mirror_engine, state_cache_manager=state_cache, on_complete=_on_ignition_complete)
                app.pack(fill=tk.BOTH, expand=True)
                self.shared_instances["app"] = app
                self.root.update()
        except Exception:
            logger.exception(f"🖥️🎨 [UI] App Launch Failure:\n{traceback.format_exc()}")
            self.shutdown_coordinator.on_closing()
