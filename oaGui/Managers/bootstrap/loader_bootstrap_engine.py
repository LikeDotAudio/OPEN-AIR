# Managers/loader_bootstrap_engine.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1001.1
#
# Description: Non-blocking initialization sequence for UI and Comms.

import time
from loguru import logger

from .communication_initializer import initialize_communications
from .protocol_service_igniter import ignite_protocol_services
from .control_link_assembler import assemble_system_control_links
from .application_launcher import launch_workspace_application

class LoaderBootstrapEngine:
    """
    Manages the non-blocking initialization sequence for UI and Comms.
    Consumes atomic services for modular startup.
    """

    def __init__(self, root, splash, services, app_constants, loader_shutdown_service):
        self.root = root
        self.splash = splash
        self.services = services
        self.app_constants = app_constants
        self.loader_shutdown_service = loader_shutdown_service
        self.start_time = time.time()
        self.MIN_SPLASH_TIME = 10.0

    def run(self):
        """Executes the async startup sequence using atomic services."""
        try:
            services = self.services

            # Phase 1: Communication
            initialize_communications(
                self.splash, services["mqtt_conn"], services["sub_router"], services["state_cache"]
            )

            # Phase 2: Protocols
            ignite_protocol_services(self.splash, services)

            # Phase 3: External (Placeholder for future expansion)

            # Phase 4: Control Links
            assemble_system_control_links(services["sub_router"], services["splinker_manager"])

            # Phase 5: Launch
            self.root.after(200, lambda: launch_workspace_application(self, services))

        except Exception as e:
            from oaLogging.Methods.matrix_gate import is_debug_allowed
            if is_debug_allowed(system="ui", element="lifecycle"):
                logger.exception("🖥️🏗️🎨 [UI] Bootstrap Failure")
            else:
                logger.error(f"🖥️🏗️🎨 [UI] Bootstrap Failure: {e}")

            self.root.after(0, self.loader_shutdown_service.on_closing)
