# Core/oid_map_converter.py
# Author: Gemini (Refactored from SNMPManager)
# Version: 20260324.1.0
#
# Description: Converts MQTT topics and payloads into SNMP OID map data.

import os
import time
import threading
from loguru import logger

# Import necessary helper functions and constants
from oaComSNMP.Methods.snmp_utils import get_snmp_node_id, get_snmp_descriptor
from oaComSNMP.Constants.snmp_constants import OID_MAP_STR_LIMIT
# Assuming SNMP_LOGGER is available and configured in the logging setup
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger 

# LOCAL_DEBUG can be set or passed if needed
LOCAL_DEBUG = True

class OidMapConverter:
    """
    Responsible for converting MQTT topics and payload data into an SNMP OID map.
    """

    def __init__(self, base_oid: str, state_cache_manager, thread_lock: threading.RLock):
        """
        Initializes the converter.
        
        Args:
            base_oid: The base OID for SNMP data.
            state_cache_manager: The manager providing access to the state cache.
            thread_lock: The RLock used by the calling manager for thread-safe access.
        """
        self.base_oid = base_oid
        self.state_cache_manager = state_cache_manager
        self._state_lock = thread_lock # Use the provided lock for external state access
        self.oid_map = {}
        
    def build_oid_map(self):
        """
        Updates the internal OID map from the state cache by processing MQTT topics.
        This method is designed to be called in a thread-safe context by the caller.
        It assumes the caller has acquired the necessary lock before calling.
        """
        if not self.state_cache_manager:
            snmp_logger.warning("OidMapConverter: State cache manager is not available.")
            return {}
        
        # Use the provided lock to access the state cache safely
        cache_snapshot = {}
        with self._state_lock: # Use the provided lock from the caller (SNMPManager)
            try:
                # If it's a dict, dict.copy() is a shallow copy, safe from concurrent size changes during iteration
                cache_snapshot = self.state_cache_manager.cache.copy()
            except AttributeError:
                # Fallback if it's not a standard dict
                cache_snapshot = dict(self.state_cache_manager.cache)

        new_oid_map = {}
        
        if LOCAL_DEBUG:
            snmp_logger.debug(f"OidMapConverter: Updating OID map. Cache size: {len(cache_snapshot)}")

        for topic, payload in cache_snapshot.items():
            # ⚡ FILTER: Skip System control/status, Router, and large Blobs
            if any(x in topic for x in ["/System/", "/Control/", "/Status/", "/Router/"]):
                continue
                
            # ⚡ FILTER: Skip GUI Initialization and Discovery metadata
            source = str(payload.get("source", "")).upper() if isinstance(payload, dict) else ""
            if source in ["GUI-INIT", "GUI-LOAD", "SYSTEM-CONFIG"]:
                continue
                
            val = payload.get("val") if isinstance(payload, dict) else payload
            val_str = str(val) if val is not None else ""
            
            # ⚡ PERFORMANCE: Skip massive blobs and nested structures
            if len(val_str) > OID_MAP_STR_LIMIT or "{" in val_str or "[" in val_str:
                continue

            parts = topic.split('/')
            if parts[0] == "OPEN-AIR": parts = parts[1:]
            
            oid_nodes = ["1"] # Base OID node for dynamic data
            path_acc = []
            for p in parts:
                path_acc.append(p)
                # Helper function to get SNMP node ID from path components
                oid_nodes.append(get_snmp_node_id(path_acc))
            
            full_oid = f"{self.base_oid}.{'.'.join(oid_nodes)}"
            # Helper function to get a human-readable descriptor
            descriptor = get_snmp_descriptor(path_acc)
            
            new_oid_map[full_oid] = {
                "topic": topic, 
                "val": val_str, 
                "descriptor": descriptor,
                "path_parts": parts # Keep original path parts for context if needed
            }
        
        self.oid_map = new_oid_map # Update internal map
        
        if LOCAL_DEBUG:
            snmp_logger.debug(f"OidMapConverter: OID map built. Active objects: {len(self.oid_map)}")
            
        return self.oid_map
