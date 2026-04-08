# oaComBroker/Managers/heartbeat_generator.py
# Author: Anthony Peter Kuzub
# Version: 20260407.1200.1
#
# Description: Dedicated 1Hz Heartbeat Generator for System-Wide Liveness.

import time
import threading
import orjson
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

class HeartbeatGenerator:
    """
    Publishes a 1Hz asynchronous pulse to 'OPEN-AIR/SYSTEM/HB'.
    Used by protocol modules for link-state verification and watchdog safety.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, mqtt_manager=None):
        if hasattr(self, "_initialized"): return
        self._initialized = True
        
        self.mqtt = mqtt_manager
        self.interval = 1.0 # 1Hz
        self._running = False
        self._thread = None
        self.topic = "OPEN-AIR/SYSTEM/HB"

    @classmethod
    def get_instance(cls, mqtt_manager=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(mqtt_manager)
            elif mqtt_manager:
                cls._instance.mqtt = mqtt_manager
        return cls._instance

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SystemHeartbeat")
        self._thread.start()
        matrix_log("system", "heartbeat", "start", f"💓 [HEARTBEAT] System Pulse Active on {self.topic}", "INFO")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        matrix_log("system", "heartbeat", "stop", "🛑 [HEARTBEAT] System Pulse Stopped.", "INFO")

    def _loop(self):
        while self._running:
            try:
                if self.mqtt:
                    payload = {
                        "ts": time.time(),
                        "src": "HEARTBEAT",
                        "val": "PULSE",
                        "guid": app_constants.INSTANCE_GUID,
                        "msg_type": "HEARTBEAT"
                    }
                    # Heartbeats bypass the router and go direct to MQTT
                    self.mqtt.publish(self.topic, orjson.dumps(payload).decode(), retain=False)
            except Exception as e:
                matrix_log("system", "heartbeat", "_loop", f"❌ [HEARTBEAT] Error: {e}", "ERROR")
            
            time.sleep(self.interval)

def start_heartbeat(mqtt_manager):
    generator = HeartbeatGenerator.get_instance(mqtt_manager)
    generator.start()
    return generator
