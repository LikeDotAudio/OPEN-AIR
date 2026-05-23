# oaGui/Managers/display/app_shutdown_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for handling the graceful shutdown of the GUI application.

from oaLogging.Methods.matrix_gate import matrix_log


def orchestrate_app_shutdown(display_instance):
    """Initiates application-wide shutdown procedures."""
    matrix_log("ui", "gui_shell", "shutdown", "🛑 Initiating application shutdown...", "DEBUG")

    if hasattr(display_instance, 'mqtt_connection_manager') and display_instance.mqtt_connection_manager:
        display_instance.mqtt_connection_manager.disconnect()

    if hasattr(display_instance, 'visa_proxy') and display_instance.visa_proxy:
        display_instance.visa_proxy.shutdown()
