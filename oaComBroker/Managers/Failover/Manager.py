# oaComBroker/Managers/Failover/Manager.py
#
# Orchestrates high-availability failover state for redundant instances.
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
# Version 20260330.1600.1

import time
import threading
import orjson
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log
app_constants = Config.get_instance()

class FailoverManager:
    """
    Elects and maintains the 'Primary' state of the local instance.
    """
    def __init__(self, protocol_router, mqtt_manager):
        self.router = protocol_router
        self.mqtt = mqtt_manager
        self.guid = app_constants.INSTANCE_GUID
        
        self.is_active = True
        self._running = False
        self._peers = {} 
        self._lock = threading.Lock()
        
        self.HEARTBEAT_INTERVAL = 1.0  
        self.FAILOVER_TIMEOUT = 3.5    
        
        self.topic_root = "OPEN-AIR/System/Failover"
        self.partition = app_constants.PARTITION_ID
        self.heartbeat_topic = f"{self.topic_root}/{self.partition}/Heartbeat/{self.guid}"
        self.discovery_topic = f"{self.topic_root}/{self.partition}/Heartbeat/#"
        self.status_topic = f"{self.topic_root}/{self.partition}/Status/{self.guid}"
        self._start_ts = time.time()

    def start(self):
        if self._running: return
        self._running = True
        
        existing_callback = self.mqtt.on_message_callback
        def failover_message_handler(client, userdata, message):
            if existing_callback: 
                try: existing_callback(client, userdata, message)
                except Exception: pass
            self._on_heartbeat(message)
            
        self.mqtt.on_message_callback = failover_message_handler
        self.mqtt.subscribe(self.discovery_topic)
        
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        
        if app_constants.ROUTER_FAILOVER_LOGS:
                matrix_log("comms", "broker", "start", 
                   f"🛡️ [FAILOVER] Manager active. Instance: {self.guid}", "INFO")

    def _heartbeat_loop(self):
        while self._running:
            try:
                payload = {
                    "guid": self.guid,
                    "active": self.is_active,
                    "start_ts": self._start_ts,
                    "timestamp": time.time()
                }
                self.mqtt.publish(self.heartbeat_topic, 
                                 orjson.dumps(payload).decode(), retain=False)
            except Exception: pass
            time.sleep(self.HEARTBEAT_INTERVAL)

    def _on_heartbeat(self, message):
        if "System/Failover/Heartbeat/" in message.topic:
            try:
                data = orjson.loads(message.payload)
                peer_guid = data.get("guid")
                if peer_guid and peer_guid != self.guid:
                    with self._lock:
                        self._peers[peer_guid] = {
                            "timestamp": time.time(),
                            "start_ts": data.get("start_ts", time.time())
                        }
            except Exception: pass

    def _monitor_loop(self):
        while self._running:
            now = time.time()
            with self._lock:
                dead_peers = [g for g, p in self._peers.items() 
                              if (now - p["timestamp"]) > self.FAILOVER_TIMEOUT]
                for g in dead_peers:
                    del self._peers[g]
                    if app_constants.ROUTER_FAILOVER_LOGS:
                            matrix_log("comms", "broker", "_monitor_loop", 
                               f"💀 [FAILOVER] Peer {g} lost.", "WARNING")

                candidates = [{"guid": self.guid, "start_ts": self._start_ts}]
                for g, p in self._peers.items():
                    candidates.append({"guid": g, "start_ts": p["start_ts"]})
                
                candidates.sort(key=lambda x: (x["start_ts"], x["guid"]))
                
                winner = candidates[0]["guid"]
                should_be_active = (winner == self.guid)

            if should_be_active != self.is_active:
                self._transition_state(should_be_active)
            
            time.sleep(0.5)

    def _transition_state(self, become_active):
        self.is_active = become_active
        role = "PRIMARY" if become_active else "SHADOW"
        
        try:
            status_payload = {"guid": self.guid, "role": role, 
                              "active": become_active}
            self.mqtt.publish(self.status_topic, 
                             orjson.dumps(status_payload).decode(), retain=True)
        except Exception: pass

        if become_active:
            if app_constants.ROUTER_FAILOVER_LOGS:
                    matrix_log("comms", "broker", "_transition_state", 
                       "👑 [FAILOVER] Promoted to MASTER.", "SUCCESS")
            self._set_router_state(True)
        else:
            if app_constants.ROUTER_FAILOVER_LOGS:
                    matrix_log("comms", "broker", "_transition_state", 
                       "💤 [FAILOVER] Entering passive SHADOW mode.", "INFO")
            self._set_router_state(False)

    def _set_router_state(self, active):
        if hasattr(self.router, "set_active_state"):
            self.router.set_active_state(active)
