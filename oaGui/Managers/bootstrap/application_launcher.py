# oaGui/Managers/bootstrap/application_launcher.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Final phase service for building and revealing the main application workspace.

import time
import tkinter as tk
from loguru import logger

def launch_workspace_application(bootstrap_instance, services):
    """Orchestrates the physical assembly and visibility of the main application window."""
    try:
        bootstrap_instance.splash.set_status(message="Building Workspace...")
        from oaGui.Entry import EngineGuiDisplay
        from oaGui.Interface.viewport.tab_physical_window import TabWindowManager

        bootstrap_instance.splash.hide()
        bootstrap_instance.root.update_idletasks()

        with services["mirror_engine"].suspend_bindings():
            def _on_ignition_complete():
                _manage_post_ignition_feedback(bootstrap_instance)

            try:
                app = EngineGuiDisplay(
                    parent=bootstrap_instance.root,
                    root=bootstrap_instance.root,
                    mqtt_connection_manager=services["mqtt_conn"],
                    subscriber_router=services["sub_router"],
                    state_mirror_engine=services["mirror_engine"],
                    state_cache_manager=services["state_cache"],
                    osc_manager=services.get("osc_manager"),
                    snmp_manager=services.get("snmp_manager"),
                    midi_manager=services.get("midi_manager"),
                    on_complete=_on_ignition_complete
                )
                app.pack(fill=tk.BOTH, expand=True)
                services["app"] = app
                bootstrap_instance.root.update_idletasks()
            except tk.TclError:
                logger.exception("🖥️🏗️🎨 [UI] TclError during EngineGuiDisplay build")
                raise

    except Exception:
        logger.exception("🖥️🏗️🎨 [UI] App Launch Failure")
        bootstrap_instance.root.after(0, bootstrap_instance.loader_shutdown_service.on_closing)

def _manage_post_ignition_feedback(bootstrap_instance):
    """Handles the multi-phase visual feedback after the GUI build is complete."""
    elapsed = time.time() - bootstrap_instance.start_time
    remaining = max(0, bootstrap_instance.MIN_SPLASH_TIME - elapsed)
    phase_ms = int((remaining / 3.0) * 1000)

    def _finish():
        from oaGui.Interface.viewport.tab_physical_window import TabWindowManager
        try:
            bootstrap_instance.splash.set_status(message="Ignition Complete!")
            TabWindowManager.reveal_main_window(
                bootstrap_instance.root, 
                bootstrap_instance.splash, 
                bootstrap_instance.app_constants.global_settings["debug_enabled"]
            )
            bootstrap_instance.services["mirror_engine"]._schedule_queue_processing()
        except Exception:
            logger.exception("🖥️🏗️🎨 [UI] Ignition Finalization Failure")
            bootstrap_instance.root.after(0, bootstrap_instance.loader_shutdown_service.on_closing)

    def _phase_2():
        bootstrap_instance.splash.set_status(message="Ignition Phase 2: Building systems...")
        bootstrap_instance.root.after(phase_ms, _phase_3)

    def _phase_3():
        bootstrap_instance.splash.set_status(message="Ignition Phase 3: Finalizing...")
        bootstrap_instance.root.after(phase_ms, _finish)

    bootstrap_instance.splash.set_status(message="Ignition Phase 1: Warming up...")
    bootstrap_instance.root.after(phase_ms, _phase_2)
