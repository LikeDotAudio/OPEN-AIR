# oaComProtocols.oaComSMPTE2138/Managers/smpte2138_monitor_manager.py
#
# Monitors the external st2138/ Protobuf tree and publishes decoded 
# human-readable updates to the internal OPEN-AIR monitor bus.
# Now enhanced with high-performance telemetry and heartbeat tracking.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260330.1600.1

import orjson
import sys
import os
import time
import threading
from pathlib import Path
from loguru import logger
from typing import Callable, List

LOCAL_DEBUG = False

# --- Path Guard for Protobuf Imports ---
interface_path = Path(__file__).resolve().parents[2] / "oaComProtocols.oaComSMPTE2138" / "Interface"
if str(interface_path) not in sys.path:
    sys.path.insert(0, str(interface_path))

# --- Protobuf Imports ---
from oaComProtocols.oaComSMPTE2138.Interface import param_pb2
from oaComProtocols.oaComSMPTE2138.Interface import device_pb2

# --- OPEN-AIR Imports ---
from oaLogging.Core.logger import SMPTE2138_LOGGER
from oaLogging.Methods.matrix_gate import matrix_log
from oaComProtocols.oaComMQTT.Managers.mqtt_connection import MqttConnectionManager
from oaComProtocols.oaComMQTT.Managers.mqtt_subscriber_router import MqttSubscriberRouter
from oaComBroker.Core.event_bus import event_bus

def _is_debug():
    from oaLogging.Methods.matrix_gate import is_debug_allowed
    return is_debug_allowed(system="comms", element="smpte2138")

class SMPTE2138MonitorManager:
    """
    Decodes binary ST 2138 traffic and broadcasts it for GUI visualization.
    Tracks throughput and engine health to demonstrate system performance.
    """

    def __init__(self, mqtt_connection: MqttConnectionManager, 
                 subscriber_router: MqttSubscriberRouter):
        self.mqtt = mqtt_connection
        self.router = subscriber_router
        
        # Performance Telemetry
        self.stats = {
            "total_messages": 0,
            "params_processed": 0,
            "cmds_processed": 0,
            "start_time": time.time(),
            "last_msg_ts": 0,
            "throughput_msg_sec": 0.0,
            "status": "STOPPED"
        }
        
        self._setup_subscriptions()
        self._is_running = False
        self._heartbeat_thread = None
        self._observers = [] # For lazy loading

    def start(self):
        """Starts the monitor heartbeat and enables processing."""
        if not self._is_running:
            self._is_running = True
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True, name="SMPTE2138-MonitorHeartbeat")
            self._heartbeat_thread.start()
            self.stats["status"] = "RUNNING"
            matrix_log("comms", "smpte2138", "monitor_start", "✅ [MONITOR] SMPTE2138 Monitor engine started and running.", "SUCCESS")

    def stop(self):
        """Signals the monitor to stop but retains its initialized state."""
        self._is_running = False
        # Do not join to avoid blocking the main thread during shutdown
        self.stats["status"] = "STOPPED"
        
    def add_observer(self, callback: callable):
        """Registers a listener for decoded traffic."""
        if callback not in self._observers:
            self._observers.append(callback)

    def _setup_subscriptions(self):
        """
        Subscribes to the entire SMPTE2138 external tree, internal events, and bridge health.
        """
        # 1. Traffic Monitoring (External + Internal)
        self.router.subscribe_to_topic("st2138/#", self._on_smpte2138_traffic)
        self.router.subscribe_to_topic("OPEN-AIR/#", self._on_smpte2138_traffic)
        
        # 2. Bridge Status Monitoring
        self.router.subscribe_to_topic("OPEN-AIR/System/Status/SMPTE2138/Bridge", self._on_bridge_status)
        
        matrix_log("comms", "smpte2138", "_setup_subscriptions", "👂 [LISTEN] Monitor active and listening for st2138/# and OPEN-AIR/#.", "DEBUG")

    def _on_bridge_status(self, msg):
        """Updates internal status from bridge broadcasts."""
        try:
            data = msg.get_json_payload()
            if "status" in data:
                self.stats["status"] = data["status"]
                # Trigger a broadcast to update GUI immediately
                self._broadcast("STATUS_UPDATE", {"_msg_type": "STATUS", "_stats": self.get_telemetry()})
        except Exception: pass

    def _heartbeat_loop(self):
        """Periodically notifies GUI observers even if no messages are flowing."""
        while self._is_running:
            try:
                # Update throughput even when idle
                now = time.time()
                elapsed = now - self.stats["start_time"]
                if elapsed > 0:
                    self.stats["throughput_msg_sec"] = round(self.stats["total_messages"] / elapsed, 2)
                
                # Push telemetry to GUI
                self._broadcast("HEARTBEAT", {"_msg_type": "HEARTBEAT", "_stats": self.get_telemetry()})
            except Exception: pass
            time.sleep(1.0)

    def _on_smpte2138_traffic(self, msg):
        """
        Intercepts binary SMPTE2138 traffic and updates performance metrics.
        """
        topic = msg.topic
        payload = msg.payload
        now = time.time()
        
        self.stats["total_messages"] += 1
        self.stats["last_msg_ts"] = now
        
        decoded_data = None
        message_type = "Unknown"

        try:
            if "/param/" in topic:
                message_type = "SingleSetValue"
                self.stats["params_processed"] += 1
                decoded = param_pb2.SingleSetValuePayload()
                decoded.ParseFromString(payload)
                decoded_data = {
                    "slot": decoded.slot,
                    "oid": decoded.value.oid,
                    "value": self._extract_value(decoded.value.value)
                }
            elif "/cmd/" in topic:
                message_type = "ExecuteCommand"
                self.stats["cmds_processed"] += 1
                decoded = param_pb2.ExecuteCommandPayload()
                decoded.ParseFromString(payload)
                decoded_data = {
                    "slot": decoded.slot,
                    "oid": decoded.oid,
                    "value": self._extract_value(decoded.value),
                    "respond": decoded.respond
                }
            
            if decoded_data:
                decoded_data["_msg_type"] = message_type
                decoded_data["_topic"] = topic
                decoded_data["_stats"] = self.get_telemetry()
                self._broadcast(topic, decoded_data)
                
        except Exception as e:
            if LOCAL_DEBUG:
                SMPTE2138_LOGGER.trace(f"⚠️ [MONITOR] Decode skipped for {topic}: {e}")

    def _extract_value(self, value_obj):
        """Helper to extract the active field from a SMPTE2138 Value object."""
        kind = value_obj.WhichOneof("kind")
        if not kind: return None
        return getattr(value_obj, kind)

    def get_telemetry(self):
        """Returns the current performance and health snapshot."""
        uptime = time.time() - self.stats["start_time"]
        return {
            "uptime_s": round(uptime, 1),
            "msg_count": self.stats["total_messages"],
            "rate": self.stats["throughput_msg_sec"],
            "broker": f"{self.mqtt.broker_address}:{self.mqtt.broker_port}",
            "connected": self.mqtt.is_connected(),
            "status": self.stats["status"]
        }

    def _broadcast(self, topic, data):
        """Notifies all registered observers of the decoded packet and stats."""
        event_bus.publish("SMPTE2138_TRAFFIC", topic=topic, data=data)
