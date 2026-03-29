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
# Version 20260328.1600.1
#
# Description:
# This module implements the Failover Management logic for the OPEN-AIR
# Communication Broker. It ensures that only one instance in a redundant
# cluster acts as the 'Primary Master' at any given time, preventing
# hardware control collisions and network loops.
#
# Partitioned Architecture (Core vs UI):
# This is a 'Manager' level service. It coordinates between the Core 
# ProtocolRouter (which handles physical I/O) and the MQTT network. It does
# not contain UI logic but provides status updates for UI consumption.
#
# Constraints & Dependencies:
# - Requires a functional MqttConnectionManager for heartbeat broadcasts.
# - Assumes a unique INSTANCE_GUID is available in the global configuration.
# - Depends on the 'OPEN-AIR/System/Failover' MQTT topic namespace.

import time
import threading
import orjson
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()
failover_logger = logger.bind(subsystem="FAILOVER")

class FailoverManager:
    """
    Elects and maintains the 'Primary' state of the local instance.
    
    The FailoverManager uses a 'Lowest-Start-Time' election algorithm.
    Instances broadcast heartbeats via MQTT. The instance with the 
    earliest boot time (or lowest GUID in case of a tie) is promoted
    to PRIMARY.
    """
    def __init__(self, protocol_router, mqtt_manager):
        """
        Initializes the Failover Manager state.
        
        Args:
            protocol_router (ProtocolRouter): Reference to the Core hub.
            mqtt_manager (MqttManager): Transport for heartbeat traffic.
            
        Side Effects:
            - Allocates internal peer tracking dictionary.
            - Defines MQTT topic strings based on instance GUID.
        """
        self.router = protocol_router
        self.mqtt = mqtt_manager
        self.guid = app_constants.INSTANCE_GUID
        
        self.is_active = False
        self._running = False
        self._peers = {} # GUID -> last_seen_ts data
        self._lock = threading.Lock()
        
        # Timing Constants (GNU Standard: No Magic Numbers)
        self.HEARTBEAT_INTERVAL = 1.0  # Seconds between local heartbeats
        self.FAILOVER_TIMEOUT = 3.5    # Seconds before a peer is dead
        
        self.topic_root = "OPEN-AIR/System/Failover"
        self.heartbeat_topic = f"{self.topic_root}/Heartbeat/{self.guid}"
        self.discovery_topic = f"{self.topic_root}/Heartbeat/#"
        self.status_topic = f"{self.topic_root}/Status/{self.guid}"
        self._start_ts = time.time()

    def start(self):
        """
        Activates the failover loops and registers MQTT listeners.
        
        Returns:
            None. Success is indicated by the start of background threads.
            
        Side Effects:
            - Spawns two background threads (Heartbeat and Monitor).
            - Subscribes to the Failover discovery MQTT topic.
            - Wraps the existing MQTT message callback.
        """
        if self._running: return
        self._running = True
        
        # Register heartbeat handler
        existing_callback = self.mqtt.on_message_callback
        def failover_message_handler(client, userdata, msg):
            if existing_callback: 
                try: existing_callback(client, userdata, msg)
                except Exception: pass
            self._on_heartbeat(msg)
            
        self.mqtt.on_message_callback = failover_message_handler
        self.mqtt.subscribe(self.discovery_topic)
        
        # Start maintenance and heartbeat threads
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        
        failover_logger.info(f"🛡️ [FAILOVER] Manager active. Instance: {self.guid}")

    def _heartbeat_loop(self):
        """
        Periodically broadcasts local liveness and state to peers.
        
        Runs in a background thread. Failures in publication are caught
        to prevent thread termination.
        """
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

    def _on_heartbeat(self, msg):
        """
        Parses incoming peer heartbeats and updates the local registry.
        
        Args:
            msg (MQTTMessage): The raw message from the broker.
            
        Side Effects:
            - Updates the thread-safe self._peers dictionary.
        """
        if "System/Failover/Heartbeat/" in msg.topic:
            try:
                data = orjson.loads(msg.payload)
                peer_guid = data.get("guid")
                # Update peer timestamp and start time if not self.
                if peer_guid and peer_guid != self.guid:
                    with self._lock:
                        self._peers[peer_guid] = {
                            "ts": time.time(),
                            "start_ts": data.get("start_ts", time.time())
                        }
            except Exception: pass

    def _monitor_loop(self):
        """
        Maintains the peer registry and executes the Master election.
        
        This loop runs every 500ms. It prunes stale peers and determines
        if the local instance should transition between Primary and Shadow.
        """
        while self._running:
            now = time.time()
            with self._lock:
                # 1. Prune dead peers (Timeout)
                dead_peers = [g for g, p in self._peers.items() 
                              if (now - p["ts"]) > self.FAILOVER_TIMEOUT]
                for g in dead_peers:
                    del self._peers[g]
                    failover_logger.warning(f"💀 [FAILOVER] Peer {g} lost.")

                # 2. Election Logic
                # Master = Earliest boot time (start_ts).
                candidates = [{"guid": self.guid, "start_ts": self._start_ts}]
                for g, p in self._peers.items():
                    candidates.append({"guid": g, "start_ts": p["start_ts"]})
                
                # Sort by start_ts (primary) then GUID (secondary tie-breaker).
                candidates.sort(key=lambda x: (x["start_ts"], x["guid"]))
                
                winner = candidates[0]["guid"]
                should_be_active = (winner == self.guid)

            # Only transition if the election result changed.
            if should_be_active != self.is_active:
                self._transition_state(should_be_active)
            
            time.sleep(0.5)

    def _transition_state(self, become_active):
        """
        Executes the logic to promote or demote the local instance.
        
        Args:
            become_active (bool): True to become Primary, False for Shadow.
            
        Side Effects:
            - Calls set_active_state(bool) on the ProtocolRouter.
            - Publishes a state change status message to MQTT.
        """
        self.is_active = become_active
        role = "PRIMARY" if become_active else "SHADOW"
        
        # Inform the network of our role change (Retained message).
        try:
            status_payload = {"guid": self.guid, "role": role, 
                              "active": become_active}
            self.mqtt.publish(self.status_topic, 
                             orjson.dumps(status_payload).decode(), retain=True)
        except Exception: pass

        if become_active:
            failover_logger.success(f"👑 [FAILOVER] Promoted to MASTER.")
            self._set_router_state(True)
        else:
            failover_logger.info(f"💤 [FAILOVER] Entering passive SHADOW mode.")
            self._set_router_state(False)

    def _set_router_state(self, active):
        """
        Instructs the Router to enable or disable hardware egress.
        
        Args:
            active (bool): Desired state for the router pipeline.
        """
        if hasattr(self.router, "set_active_state"):
            self.router.set_active_state(active)
