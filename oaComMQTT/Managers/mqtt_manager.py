# Managers/mqtt_manager.py
#
# Manages MQTT-related system operations: Broker Monitoring, Topic Management, 
# and Service Control. Acts as the back-end orchestrator for system status.
#
# Author: Anthony Peter Kuzub
# Version: 20260330.1600.2

import time
import orjson
import threading
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
from oaComMQTT.Core.mqtt_message import MqttMessage
from oaComMQTT.Methods.delete_open_air import delete_open_air_tree
import oaOchestration.Constants.project_paths as app_paths
from oaLogging.Methods.matrix_gate import matrix_log, is_debug_allowed

def _is_debug():
    return is_debug_allowed(system="comms", element="mqtt")

app_constants = Config.get_instance()

def register_service(mqtt_client, state_cache, broker_address, broker_port, client_id, service_name, data):
    """Placeholder for service registration logic."""
    matrix_log("comms", "mqtt", "register_service", f"🔧 [MQTT] Registering service: {service_name}", "INFO")
    # Implementation logic for registering a service

def re_register_all_services(mqtt_client, state_cache):
    """Placeholder for re-registering all services."""
    matrix_log("comms", "mqtt", "re_register_all_services", "🔧 [MQTT] Re-registering all services", "INFO")
    # Implementation logic for re-registering all services

class MqttManager:
    """
    Back-end manager for the MQTT Dashboard and System Status.
    """
    def __init__(self, subscriber_router, mqtt_client, state_cache_manager):
        self.subscriber_router = subscriber_router
        self.mqtt_client = mqtt_client
        self.state_cache_manager = state_cache_manager
        
        self._is_running = False
        self._thread = None
        
        # Subscribe to Control Topics
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Broker/Delete/#", self._handle_delete_command)
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Broker/Service/#", self._handle_service_command)
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Status/Fleet/Complete", self._on_fleet_scan_complete)
        
        matrix_log("comms", "mqtt", "__init__", "🚀 [MQTT] MqttManager initialized.", "DEBUG")

    def start(self):
        """Starts the MQTT manager background threads."""
        if self._is_running:
            return
        
        self._is_running = True
        self._thread = threading.Thread(target=self._system_status_loop, daemon=True, name="MQTT-StatusPoller")
        self._thread.start()
        matrix_log("comms", "mqtt", "start", "🚀 [MQTT] MqttManager started.", "INFO")

    def stop(self):
        """Stops the background threads and cleans up."""
        self._is_running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        matrix_log("comms", "mqtt", "stop", "MQTT: MqttManager stopped.", "INFO")

    def _publish_status(self, status: str):
        """Publishes the connection status to the broker."""
        status_payload = {
            "val": status,
            "status": status,
            "address": app_constants.MQTT_BROKER_ADDRESS,
            "port": str(app_constants.MQTT_BROKER_PORT)
        }
        status_json = orjson.dumps(status_payload)
        self.mqtt_client.publish("OPEN-AIR/System/Status/Broker/Connection", status_json, qos=1)

    def _system_status_loop(self):
        """Periodically prepares connection status and system paths."""
        while self._is_running:
            try:
                if self.mqtt_client and self.mqtt_client.is_connected():
                    self._publish_status("ONLINE")
                    
                    # Publish Paths
                    paths_payload = {
                        "root": str(app_paths.GLOBAL_PROJECT_ROOT),
                        "markers": str(app_paths.MARKERS_JSON_PATH),
                        "device_state": str(app_paths.DEVICE_STATE_CACHE_PATH),
                        "fleet": str(app_paths.STATE_VISA_FLEET_JSON_PATH),
                        "yak": str(app_paths.YAKETY_YAK_REPO_PATH),
                        "presets": str(app_paths.PRESET_REPO_PATH)
                    }
                    self.mqtt_client.publish("OPEN-AIR/System/Status/Paths", orjson.dumps(paths_payload), qos=1)
                else:
                    self._publish_status("OFFLINE")
                    self._attempt_reconnect()

            except Exception as e:
                matrix_log("comms", "mqtt", "_system_status_loop", f"🚀 [MQTT] ERROR: Status loop failed: {e}", "ERROR")
            
            time.sleep(5)

    def _attempt_reconnect(self):
        """Attempts to reconnect the MQTT client if disconnected."""
        matrix_log("comms", "mqtt", "_attempt_reconnect", "📡 [MQTT] Attempting to reconnect...", "INFO")
        try:
            res = self.mqtt_client.connect(
                app_constants.MQTT_BROKER_ADDRESS,
                app_constants.MQTT_BROKER_PORT,
                app_constants.MQTT_CLIENT_ID
            )
            if res == 0:
                self._publish_status("ONLINE")
                self.mqtt_client.loop_start()
                self._sync_state_on_reconnect()
            else:
                self._publish_status("OFFLINE")
        except Exception as e:
            matrix_log("comms", "mqtt", "_attempt_reconnect", f"📡 [MQTT] Reconnect failed: {e}", "ERROR")
            self._publish_status("OFFLINE")
            self.mqtt_client.disconnect()
            raise e

    def _sync_state_on_reconnect(self):
        """Synchronizes state and re-subscribes after a successful reconnection."""
        matrix_log("comms", "mqtt", "_sync_state_on_reconnect", "📡 [MQTT] Synchronizing state on reconnect.", "INFO")
        self.state_cache_manager.sync_state_from_all_sources()
        if hasattr(self.subscriber_router, 'resubscribe_all'):
            self.subscriber_router.resubscribe_all()
        
        # Manually ensure all known subscriptions are active on the new client instance
        if hasattr(self.subscriber_router, 'get_all_subscriptions'):
            subs = self.subscriber_router.get_all_subscriptions()
            for topic, (callback, qos) in subs.items():
                self.mqtt_client.subscribe(topic, qos)

    def _handle_delete_command(self, msg: MqttMessage):
        matrix_log("comms", "mqtt", "_handle_delete_command", "🧨 [MQTT] MqttManager: Executing Topic Deletion.", "DEBUG")
        delete_open_air_tree(self.mqtt_client, self.state_cache_manager)

    def _handle_service_command(self, msg: MqttMessage):
        try:
            payload = msg.payload
            data = orjson.loads(payload) if isinstance(payload, (bytes, str)) else payload
            action = data.get("action")
            service_name = data.get("service")
            
            matrix_log("comms", "mqtt", "_handle_service_command", f"🔧 [MQTT] MqttManager: Requested service {action}.", "DEBUG")
            
            if action == "register" and service_name:
                register_service(
                    self.mqtt_client, self.state_cache_manager,
                    app_constants.MQTT_BROKER_ADDRESS, app_constants.MQTT_BROKER_PORT,
                    app_constants.MQTT_CLIENT_ID, service_name, data.get("data", {})
                )
            elif action == "reregister_all":
                re_register_all_services(self.mqtt_client, self.state_cache_manager)
            elif action == "status" and service_name:
                self._update_service_status(service_name, data.get("status", "UNKNOWN"))
                
        except Exception as e:
            matrix_log("comms", "mqtt", "_handle_service_command", f"MQTT: Service command parse error: {e}", "ERROR")

    def _update_service_status(self, service: str, status: str):
        """Placeholder for updating service status."""
        matrix_log("comms", "mqtt", "_update_service_status", f"🔧 [MQTT] Updating status for {service} to {status}", "INFO")

    def _on_fleet_scan_complete(self, msg: MqttMessage):
        matrix_log("comms", "mqtt", "_on_fleet_scan_complete", "✅ [MQTT] MqttManager: Fleet Scan Complete detected.", "INFO")
