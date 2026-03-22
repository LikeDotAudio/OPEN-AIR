# Managers/mqtt_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260219.Performance.1
#
# Description: Manages MQTT-related system operations: Broker Monitoring, Topic Management, and Service Control.

import time
import orjson
import threading
import queue
from oaComMQTT.Workers.broker_monitor import BrokerMonitor
from oaComMQTT.Methods.delete_open_air import delete_open_air_tree
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
from oaComMQTT.Core.mqtt_message import MqttMessage
import oaOchestration.Constants.project_paths as app_paths

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

app_constants = Config.get_instance()

class MqttManager:
    """
    Back-end manager for the MQTT Dashboard and System Status.
    OPTIMIZED: Background publisher thread to prevent synchronous send latency.
    """
    def __init__(self, subscriber_router, mqtt_client, state_cache_manager):
        self.subscriber_router = subscriber_router
        self.mqtt_client = mqtt_client
        self.state_cache_manager = state_cache_manager
        
        # ⚡ OPTIMIZATION: Async Publishing Queue
        self._publish_queue = queue.Queue()
        self._is_running = True
        
        # 1. Initialize Monitor (DISABLED - Redundant Traffic)
        # self.monitor = BrokerMonitor(self.subscriber_router)
        # self.monitor.register_observer(self._on_stats_updated)
        self.monitor = None
        
        # 2. Subscribe to Control Topics
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Broker/Delete/#", self._handle_delete_command)
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/Broker/Service/#", self._handle_service_command)
        
        # Listen for Fleet Scan Completion to rebuild command tabs
        self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Status/Fleet/Complete", self._on_fleet_scan_complete)
        
        # 3. Dedicated Async Worker Threads
        self._status_thread = threading.Thread(target=self._system_status_loop, daemon=True, name="MQTT_Status_Poller")
        self._pub_thread = threading.Thread(target=self._publish_worker, daemon=True, name="MQTT_Async_Publisher")
        
        self._status_thread.start()
        self._pub_thread.start()
        
        if LOCAL_DEBUG:
            logger.debug("🚀📤📥 [MQTT] MqttManager initialized with Async "
                         "Publisher.")

    def _publish_async(self, topic, payload, retain=False):
        """Queues a message for background publishing."""
        self._publish_queue.put((topic, payload, retain))

    def _publish_worker(self):
        """Background thread that performs the actual MQTT sends."""
        while self._is_running:
            try:
                topic, payload, retain = self._publish_queue.get(timeout=1.0)
                if self.mqtt_client and self.mqtt_client.is_connected():
                    self.mqtt_client.publish(topic, payload, retain=retain)
                self._publish_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Gravity of Errors: Non-gated failure reporting.
                logger.error(f"🚀🚫🛑 [MQTT] ERROR: Publish worker failed: {e}")

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
                    self._publish_async("OPEN-AIR/System/Status/Broker/Connection", status_json)
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
                    self._publish_async("OPEN-AIR/System/Status/Paths", paths_json)
                    last_paths_payload = paths_json

            except Exception as e:
                # Gravity of Errors: Non-gated failure reporting.
                logger.error(f"🚀🚫🛑 [MQTT] ERROR: Status loop failed: {e}")
            
            time.sleep(5) 

    #     """Called by BrokerMonitor. Enqueues stats for async publishing."""
    #     formatted_stats = {}
    #             try:
    #                 seconds = int(float(val))
    #                 val = time.strftime("%H:%M:%S", time.gmtime(seconds))
    #             except: pass
    #         formatted_stats[key] = val
    #         
    #     self._publish_async("OPEN-AIR/System/Status/Broker/Stats", orjson.dumps(formatted_stats).decode())

    def _handle_delete_command(self, msg: MqttMessage):
        if LOCAL_DEBUG:
            logger.debug("🧨💣🔥 [MQTT] MqttManager: Executing OPEN-AIR "
                         "Topic Deletion.")
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
                logger.debug(f"🔧⚙️🛠️ [MQTT] MqttManager: Requested service "
                             f"{action}.")
        except: pass

    def _on_fleet_scan_complete(self, msg: MqttMessage):
        if LOCAL_DEBUG:
            logger.success("✅✅✅ [SUCCESS] MqttManager: Fleet Scan Complete "
                           "detected.")
        # Rebuilding logic would go here if needed in this context
        # Rebuilding logic would go here if needed in this context

    def stop(self):
        self._is_running = False
        if self.monitor:
            self.monitor.unregister_observer(self._on_stats_updated)
