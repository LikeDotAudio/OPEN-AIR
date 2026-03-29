# Managers/mqtt_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260324.1.0
#
# Description: Manages MQTT-related system operations: Broker Monitoring, Topic Management, and Service Control.

import time
import orjson
import threading
from oaComMQTT.Workers.broker_monitor import BrokerMonitor
from oaComMQTT.Methods.delete_open_air import delete_open_air_tree
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
from oaComMQTT.Core.mqtt_message import MqttMessage
import oaOchestration.Constants.project_paths as app_paths

LOCAL_DEBUG = True
app_constants = Config.get_instance()

class MqttManager:
    """
    Back-end manager for the MQTT Dashboard and System Status.
    Handles periodic system status publishing and control commands.
    """
    def __init__(self, subscriber_router, mqtt_client, state_cache_manager):
        self.subscriber_router = subscriber_router
        self.mqtt_client = mqtt_client
        self.state_cache_manager = state_cache_manager
        
        self._is_running = True
        
        # 1. Initialize Monitor (Optional/Disabled if redundant)
        self.monitor = None
        
        # 2. Subscribe to Control Topics
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Broker/Delete/#", self._handle_delete_command)
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Broker/Service/#", self._handle_service_command)
        
        # Listen for Fleet Scan Completion
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Status/Fleet/Complete", self._on_fleet_scan_complete)
        
        # 3. Dedicated System Status Thread
        self._status_thread = threading.Thread(target=self._system_status_loop, daemon=True, name="MQTT-StatusPoller")
        self._status_thread.start()
        
        if LOCAL_DEBUG:
            logger.debug("🚀 [MQTT] MqttManager initialized.")

    def _system_status_loop(self):
        """Periodically prepares connection status and system paths. Only publishes on change."""
        last_status_payload = None
        last_paths_payload = None

        while self._is_running:
            try:
                # 1. Broker Connection Status
                is_online = "ONLINE" if self.mqtt_client and self.mqtt_client.is_connected() else "OFFLINE"
                status_payload = {
                    "val": is_online,
                    "status": is_online,
                    "address": app_constants.MQTT_BROKER_ADDRESS,
                    "port": str(app_constants.MQTT_BROKER_PORT)
                }
                status_json = orjson.dumps(status_payload).decode()
                if status_json != last_status_payload:
                    self.mqtt_client.publish("OPEN-AIR/System/Status/Broker/Connection", status_json)
                    last_status_payload = status_json

                # 2. System Paths
                paths_payload = {
                    "root": str(app_paths.GLOBAL_PROJECT_ROOT),
                    "markers": str(app_paths.MARKERS_JSON_PATH),
                    "device_state": str(app_paths.DEVICE_STATE_CACHE_PATH),
                    "fleet": str(app_paths.STATE_VISA_FLEET_JSON_PATH),
                    "yak": str(app_paths.YAKETY_YAK_REPO_PATH),
                    "presets": str(app_paths.PRESET_REPO_PATH)
                }
                paths_json = orjson.dumps(paths_payload).decode()
                if paths_json != last_paths_payload:
                    self.mqtt_client.publish("OPEN-AIR/System/Status/Paths", paths_json)
                    last_paths_payload = paths_json

            except Exception as e:
                logger.error(f"🚀 [MQTT] ERROR: Status loop failed: {e}")
            
            time.sleep(5)

    def _handle_delete_command(self, msg: MqttMessage):
        if LOCAL_DEBUG:
            logger.debug("🧨 [MQTT] MqttManager: Executing Topic Deletion.")
        delete_open_air_tree(self.mqtt_client, self.state_cache_manager)

    def _handle_service_command(self, msg: MqttMessage):
        try:
            payload = msg.payload
            if isinstance(payload, (bytes, str)):
                data = orjson.loads(payload)
            else:
                data = payload
            action = data.get("action")
            if LOCAL_DEBUG:
                logger.debug(f"🔧 [MQTT] MqttManager: Requested service {action}.")
        except Exception as e:
            if LOCAL_DEBUG:
                logger.error(f"MQTT: Service command parse error: {e}")

    def _on_fleet_scan_complete(self, msg: MqttMessage):
        if LOCAL_DEBUG:
            logger.info("✅ [MQTT] MqttManager: Fleet Scan Complete detected.")

    def stop(self):
        """Stops the background threads and cleans up."""
        self._is_running = False
        if self.monitor and hasattr(self.monitor, "unregister_observer"):
            # If monitor observer pattern is used
            pass
        if LOCAL_DEBUG:
            logger.debug("MQTT: MqttManager stopping.")
