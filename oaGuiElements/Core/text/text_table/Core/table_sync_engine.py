# Core/table_sync_engine.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import orjson
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import tkinter as tk
from loguru import logger
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaComProtocols.oaComMQTT.Core import mqtt_publisher_service

class TableSyncEngine:
    """Orchestrates MQTT synchronization logic for the table widget."""

    def __init__(self, tree, item_map, device_key_map, absolute_topic, csv_service, builder_logger):
        self.tree, self.item_map, self.device_key_map = tree, item_map, device_key_map
        self.abs_topic, self.csv_svc, self.logger = absolute_topic, csv_service, builder_logger
        self.is_reading_csv = False

    def update_full(self, payload, suppress_mqtt=False):
        """Processes a full table refresh from a dictionary payload."""
        try:
            data = payload if isinstance(payload, dict) else orjson.loads(payload)
            if not isinstance(data, dict): return

            for i in self.tree.get_children(): self.tree.delete(i)
            self.item_map.clear(); self.device_key_map.clear()

            if not data:
                self.csv_svc.save(self.tree["columns"], self.item_map); return

            cols = self.tree["columns"]
            if not cols and data:
                cols = list(next(iter(data.values())).keys())
                self.tree["columns"] = cols
                for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=120, anchor="w")

            for k, v in data.items():
                iid = self.tree.insert("", tk.END, values=[v.get(c, "") for c in cols], tags=(k))
                self.item_map[iid], self.device_key_map[k] = v, iid
                if self.abs_topic and not self.is_reading_csv and not suppress_mqtt:
                    mqtt_publisher_service.publish_payload(get_topic(self.abs_topic, "data", k), orjson.dumps(v).decode())
            
            self.csv_svc.save(cols, self.item_map)
        except Exception as e: self.logger.error(f"❌ Full table update failed: {e}")

    def update_incremental(self, msg):
        """Processes a single row update or pulse event."""
        topic, payload = msg.topic, msg.payload
        try:
            data = payload if isinstance(payload, (dict, list)) else orjson.loads(payload)
        except Exception as e:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"Failed to decode payload in incremental update: {e}", level="DEBUG")
            return

        # 1. Handle Pulse (Radar Sync)
        pa = data.get("angle") or data.get("position")
        if isinstance(data, dict) and data.get("pulse") is True and pa is not None:
            tid = self.device_key_map.get(str(int(pa)))
            if not tid:
                ac = next((c for c in self.tree["columns"] if c.lower() in ["angle", "deg", "position"]), None)
                if ac:
                    for iid, idat in self.item_map.items():
                        try:
                            if abs(float(idat.get(ac)) - float(pa)) < 1.0: tid = iid; break
                        except Exception as e:
                            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"Error checking pulse match: {e}", level="TRACE")
            if tid: self.tree.selection_set(tid); self.tree.see(tid)
            return

        # 2. Handle Data Update
        if not self.abs_topic or "/data/" not in topic or not topic.startswith(self.abs_topic): return
        
        # Extract the data key (dk) which is the part after the last "/data/"
        dk = topic.split("/data/")[-1]
        if "/" in dk: return # We only want flat IDs directly after a "/data/" segment

        if not data and data is not False: # Deletion
            if dk in self.device_key_map:
                iid = self.device_key_map.pop(dk); self.item_map.pop(iid, None); self.tree.delete(iid)
            self.csv_svc.save(self.tree["columns"], self.item_map); return

        if not self.tree["columns"]:
            self.tree["columns"] = list(data.keys())
            for c in self.tree["columns"]: self.tree.heading(c, text=c); self.tree.column(c, width=120, anchor="w")

        vals = [data.get(c, "") for c in self.tree["columns"]]
        if dk in self.device_key_map:
            iid = self.device_key_map[dk]; self.tree.item(iid, values=vals); self.item_map[iid] = data
        else:
            iid = self.tree.insert("", tk.END, values=vals, tags=(dk))
            self.item_map[iid], self.device_key_map[dk] = data, iid
        self.csv_svc.save(self.tree["columns"], self.item_map)