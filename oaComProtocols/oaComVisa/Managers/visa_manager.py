# Managers/visa_manager.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Main orchestrator for VISA device interactions.

from ..Core.visa_proxy import VisaProxy
from ..Methods.visa_reboot import VisaRebootManager
from ..Methods.visa_reset import VisaResetManager
from ..Methods.visa_search_results import VisaDeviceSearcher
from ..Workers.logic_connect_instrument import VisaConnector
from ..Workers.logic_disconnect_instrument import VisaDisconnector
from ..Workers.logic_mqtt_listen import VisaMqttListener
from ..Workers.logic_mqtt_publisher import VisaGuiPublisher


class VisaManagerOrchestrator:
    def __init__(self, mqtt_connection_manager, subscriber_router):

        # Instantiate the low-level and publishing managers first
        self.visa_proxy = VisaProxy(
            mqtt_controller=mqtt_connection_manager, subscriber_router=subscriber_router
        )
        self.gui_publisher = VisaGuiPublisher(mqtt_controller=mqtt_connection_manager)

        # ⚡ TELEMETRY: Broadcast proxy availability on startup
        self.gui_publisher._publish_proxy_status("CONNECTED")

        # Instantiate the logic workers
        self.device_searcher = VisaDeviceSearcher()
        self.connector = VisaConnector(
            visa_proxy=self.visa_proxy, gui_publisher=self.gui_publisher
        )
        self.disconnector = VisaDisconnector(
            visa_proxy=self.visa_proxy, gui_publisher=self.gui_publisher
        )

        # Instantiate the main listener and inject dependencies
        self.mqtt_listener = VisaMqttListener(
            subscriber_router=subscriber_router,
            searcher=self.device_searcher,
            connector=self.connector,
            disconnector=self.disconnector,
            gui_publisher=self.gui_publisher,
        )

        # Instantiate the reset/reboot managers
        self.reset_manager = VisaResetManager(
            mqtt_connection_manager=mqtt_connection_manager,
            subscriber_router=subscriber_router,
            visa_proxy=self.visa_proxy,
        )
        self.reboot_manager = VisaRebootManager(
            mqtt_connection_manager=mqtt_connection_manager,
            subscriber_router=subscriber_router,
            visa_proxy=self.visa_proxy,
        )

    def get_managers(self):
        return {
            "visa_proxy": self.visa_proxy,
            "visa_gui_publisher": self.gui_publisher,
            "visa_device_searcher": self.device_searcher,
            "visa_connector": self.connector,
            "visa_disconnector": self.disconnector,
            "visa_mqtt_listener": self.mqtt_listener,
            "visa_reset_manager": self.reset_manager,
            "visa_reboot_manager": self.reboot_manager,
        }
