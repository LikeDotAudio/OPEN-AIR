# oaComProtocols.oaComSNMP/Core/oid_map_converter.py
#
# Converts MQTT topics and payloads into SNMP OID map data.
#
# Author: Anthony Peter Kuzub (Contributor to this project)
# Blog: www.Like.audio
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260330.1600.1

import threading

from oaComProtocols.oaComSNMP.Constants.snmp_constants import OID_MAP_STR_LIMIT

# Import necessary helper functions and constants
from oaComProtocols.oaComSNMP.Methods.snmp_utils import get_snmp_descriptor, get_snmp_node_id

# Assuming SNMP_LOGGER is available and configured in the logging setup
from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log


def _is_debug():
    return is_debug_allowed(system="comms", element="snmp")

class OidMapConverter:
    """
    Responsible for converting MQTT topics and payload data into an SNMP OID map.
    """

    def __init__(self, base_oid: str, thread_lock: threading.RLock):
        """
        Initializes the converter.
        
        Args:
            base_oid: The base OID for SNMP data.
            thread_lock: The RLock used by the calling manager for thread-safe access.
        """
        self.base_oid = base_oid
        self._state_lock = thread_lock # Use the provided lock for external state access
        self.oid_map = {}

    def build_oid_map(self, state_snapshot: dict):
        """
        Updates the internal OID map from a state snapshot (MQTT topics/payloads).
        This method is designed to be called in a thread-safe context by the caller.
        """
        new_oid_map = {}

        if _is_debug():
            matrix_log("comms", "snmp", "build_oid_map",
                       f"OidMapConverter: Updating OID map. Input size: {len(state_snapshot)}", "TRACE")

        # for topic, payload in state_snapshot.items():
        #     # ⚡ FILTER: Skip System control/status, Router, and large Blobs
        #     if any(x in topic for x in ["/System/", "/Control/", "/Status/", "/Router/"]):
        #         continue
        for topic, payload in state_snapshot.items():

            # ⚡ FILTER: Skip GUI Initialization and Discovery metadata
            source = str(payload.get("source", "")).upper() if isinstance(payload, dict) else ""
            if source in ["GUI-INIT", "GUI-LOAD", "SYSTEM-CONFIG"]:
                continue

            value = payload.get("value") if isinstance(payload, dict) else payload

            # ⚡ PERFORMANCE: Gracefully handle complex types instead of skipping
            if isinstance(value, dict):
                val_str = "DICT"
            elif isinstance(value, list):
                val_str = "LIST"
            else:
                val_str = str(value) if value is not None else ""

            if len(val_str) > OID_MAP_STR_LIMIT:
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
                "value": val_str,
                "descriptor": descriptor,
                "path_parts": parts # Keep original path parts for context if needed
            }

        self.oid_map = new_oid_map # Update internal map

        if _is_debug():
            matrix_log("comms", "snmp", "build_oid_map",
                       f"OidMapConverter: OID map built. Active objects: {len(self.oid_map)}", "TRACE")

        return self.oid_map
