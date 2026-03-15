#!/usr/bin/env python3
# managers/Display/open_air_ui.py
#
# The Dynamic UI Partition for OPEN-AIR.
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
# Version 20260314.120000.REV01

"""
open_air_ui.py - The Dynamic UI Partition for OPEN-AIR.

Purpose:
    Serves as the central orchestration point for the OPEN-AIR user interface.
    This module manages the Tkinter main loop, asynchronous bootstrapping of
    network managers, and the "Ignition" sequence for the dynamic GUI.

Responsibilities:
    - Initialize the Tkinter root environment with custom industrial themes.
    - Provide a high-fidelity Splash Screen for immediate startup feedback.
    - Bootstrap asynchronous managers for MQTT, OSC, SNMP, and MIDI without
      blocking the UI thread.
    - Implement a "State Mirroring" engine to synchronize UI widgets with
      the global MQTT state.
    - Manage a coordinated shutdown sequence to clean up all background
      communication threads.

Security Constraints:
    - Treated as an "Untrusted" partition; it cannot access Core memory.
    - Communication with the hardware core is strictly via the MQTT broker.
    - Assumes a graphical environment (X11, Wayland, or Windows GDI).
"""

import sys
import os
import time
import pathlib
import threading
import tkinter as tk

# Ensure the root directory is in the search path for local module imports.
current_dir = pathlib.Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from managers.configini.config_reader import Config
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from workers.initialization.path_initializer import initialize_paths
from managers.configini.console_encoder import configure_console_encoding

from workers.Command_Router.mqtt.mqtt_connection_manager import MqttConnectionManager
from workers.Command_Router.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.Command_Router.State_Cache.state_cache_manager import StateCacheManager
from workers.logic.state_mirror_engine import StateMirrorEngine
from workers.splash_screen.splash_screen import SplashScreen

from workers.Command_Router.OSC.osc_manager import OSCManager
from workers.Command_Router.SNMP.snmp_manager import SNMPManager
from workers.Command_Router.MIDI.midi_manager import MidiManager
from workers.Splinker.splinker_manager import SplinkerManager

# LOCAL_DEBUG: Toggles verbose tracing for the UI bootstrap sequence.
LOCAL_DEBUG = True

def _reveal_main_window(root, splash):
    """
    Swaps the Splash Screen for the Primary Application Window.

    Inputs:
        root (tk.Tk): The application root window.
        splash (SplashScreen): The active splash screen instance.
    """
    if Config.get_instance().ENABLE_DEBUG_SCREEN:
        if LOCAL_DEBUG:
            logger.debug("🖥️🎨 [UI] Reveal main window.")
    root.deiconify()
    splash.hide()

def main():
    """
    Orchestrates the startup, execution, and shutdown of the OPEN-AIR UI.

    Lead with action: Sets up the Tkinter environment, launches a non-blocking
    bootstrap thread for communication managers, and enters the main loop.

    Inputs:
        None.

    Outputs:
        None. Process terminates on window closure or OS signal.

    Side Effects:
        - Opens graphical windows.
        - Spawns background threads for asynchronous I/O.
        - Not thread-safe or reentrant.
    """
    # 1. --- Environment Initialization ---
    GLOBAL_PROJECT_ROOT, data_dir = initialize_paths()
    log_dir = pathlib.Path(data_dir) / "debug"
    set_log_directory(log_dir, partition="UI")
    configure_console_encoding()
    
    app_constants = Config.get_instance()
    
    if LOCAL_DEBUG:
        logger.debug("🖥️🎨 [UI] Starting OpenAir UI Service...")

    # 2. --- Tkinter Environment Setup ---
    root = tk.Tk()
    root.configure(bg="#2b2b2b")
    
    # Centralized Error Reporting for Tkinter Callbacks.
    def _report_callback_exception(exc, val, tb):
        import traceback
        logger.error(f"🖥️🎨 [UI] CRITICAL: Tkinter Exception:\n"
                     f"{''.join(traceback.format_exception(exc, val, tb))}")
    
    root.report_callback_exception = _report_callback_exception
    
    # Establish Global Style Defaults (Industrial Dark Theme).
    root.option_add("*Background", "#2b2b2b")
    root.option_add("*Foreground", "#dcdcdc")
    root.option_add("*Entry.background", "#3c3f41")
    root.option_add("*Entry.foreground", "#ffffff")
    root.option_add("*Text.background", "#1e1e1e")
    root.option_add("*Text.foreground", "#dcdcdc")
    
    root.title("OPEN-AIR (Partitioned UI)")
    
    # Apply OS-specific window maximization logic.
    try:
        if sys.platform.startswith("linux"):
            root.attributes("-zoomed", True)
        else:
            root.state("zoomed")
    except:
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}+0+0")
    
    # Hide the main window until the application building is complete.
    root.withdraw()
    
    # 3. --- Splash Screen Initiation ---
    splash = SplashScreen(
        root, 
        app_constants.CURRENT_VERSION, 
        app_constants.global_settings["debug_enabled"]
    )
    root.update()

    # Shared Manager Registry (to facilitate clean shutdown).
    shared_instances = {
        "app": None, "mqtt_conn": None, "state_cache": None,
        "mirror_engine": None, "osc_manager": None, "snmp_manager": None,
        "midi_manager": None, "splinker_manager": None, "protocol_router": None
    }

    def on_closing():
        """Gracefully terminates all UI and Communication sub-processes."""
        if LOCAL_DEBUG:
            logger.debug("🖥️🎨 [UI] Initiating shutdown...")
        root._shutdown = True
        
        # Sequentially stop all active managers.
        for name, instance in shared_instances.items():
            if instance:
                try:
                    # Prefer stop() or shutdown() or disconnect() methods.
                    if hasattr(instance, "stop"): instance.stop()
                    elif hasattr(instance, "shutdown"): instance.shutdown()
                    elif hasattr(instance, "disconnect"): instance.disconnect()
                except: pass
        
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 4. --- Resource Management ---
    def _periodic_gc():
        """Aggressively triggers garbage collection to keep memory lean."""
        import gc
        gc.collect()
        if not getattr(root, '_shutdown', False):
            root.after(30000, _periodic_gc)
    
    _periodic_gc()

    def _ui_bootstrap():
        """Asynchronous bootstrap logic to prevent UI thread starvation."""
        try:
            splash.set_status("Initializing Comms...")
            
            mqtt_conn = MqttConnectionManager()
            shared_instances["mqtt_conn"] = mqtt_conn
            sub_router = MqttSubscriberRouter()
            
            splash.set_status("Loading State Cache...")
            state_cache = StateCacheManager(mqtt_conn)
            state_cache.subscriber_router = sub_router
            shared_instances["state_cache"] = state_cache
            
            mirror_engine = StateMirrorEngine(
                base_topic="OPEN-AIR",
                subscriber_router=sub_router,
                root=root,
                state_cache_manager=state_cache
            )
            state_cache.state_mirror_engine = mirror_engine
            shared_instances["mirror_engine"] = mirror_engine
            
            splash.set_status("Connecting to Broker...")
            mqtt_conn.connect_to_broker(
                on_message_callback=state_cache.handle_incoming_mqtt,
                subscriber_router=sub_router
            )
            state_cache.subscribe_to_all_topics()

            # Initialize protocol-specific bridges.
            if app_constants.SCAN_OSC:
                splash.set_status("Starting OSC...")
                osc = OSCManager(state_cache, mqtt_conn, run_bridge=False)
                osc.start()
                shared_instances["osc_manager"] = osc

            if app_constants.SCAN_SNMP:
                splash.set_status("Starting SNMP...")
                snmp = SNMPManager(state_cache, mqtt_conn, run_bridge=False)
                snmp.start()
                shared_instances["snmp_manager"] = snmp

            splash.set_status("Starting MIDI...")
            midi = MidiManager(state_cache, run_bridge=False)
            midi.start()
            shared_instances["midi_manager"] = midi
            
            splash.set_status("Starting Splinker...")
            from workers.Command_Router.protocol_router import ProtocolRouter
            protocol_router = ProtocolRouter.get_instance()
            shared_instances["protocol_router"] = protocol_router
            protocol_router.set_mqtt_manager(mqtt_conn)
            protocol_router.start()
            
            splinker = SplinkerManager.get_instance(state_cache, mqtt_conn)
            protocol_router.set_splinker_manager(splinker)
            shared_instances["splinker_manager"] = splinker

            # Define high-speed Splinker-to-MQTT routing.
            def splinker_mqtt_wrapper(msg):
                splinker.handle_mqtt_command(msg.topic, msg.payload)
            sub_router.subscribe_to_topic("OPEN-AIR/System/Control/Splinker/#", 
                                          splinker_mqtt_wrapper)
            
            # --- Application Ignition (Return to UI Thread) ---
            def _launch_app():
                try:
                    splash.set_status("Building Workspace...")
                    from managers.Display.builder.gui_display import Application
                    
                    # Suspend state mirroring during build to avoid jitter.
                    with mirror_engine.suspend_bindings():
                        def _on_ignition_complete():
                            splash.set_status("Ignition Complete!")
                            def _finish():
                                _reveal_main_window(root, splash)
                                mirror_engine.start_queue_processing()
                            root.after(1, _finish)

                        app = Application(
                            parent=root, root=root,
                            mqtt_connection_manager=mqtt_conn,
                            subscriber_router=sub_router,
                            state_mirror_engine=mirror_engine,
                            state_cache_manager=state_cache,
                            on_complete=_on_ignition_complete
                        )
                        app.pack(fill=tk.BOTH, expand=True)
                        shared_instances["app"] = app
                        root.update()
                except Exception as e:
                    import traceback
                    logger.exception(f"🖥️🎨 [UI] App Launch Failure:\n"
                                     f"{traceback.format_exc()}")
                    on_closing()

            root.after(1, _launch_app)
            
        except Exception as e:
            import traceback
            logger.exception(f"🖥️🎨 [UI] Bootstrap Failure:\n"
                             f"{traceback.format_exc()}")
            root.after(0, on_closing)

    # Launch non-blocking bootstrap thread.
    threading.Thread(target=_ui_bootstrap, daemon=True).start()
    
    if LOCAL_DEBUG:
        logger.debug("🖥️🎨 [UI] Entering Tkinter MainLoop.")
    root.mainloop()

if __name__ == "__main__":
    main()
