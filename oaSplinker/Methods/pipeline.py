# Methods/pipeline.py
#
# Manages the execution pipeline for Splinker transformations.
# Orchestrates sequential data processing through a series of handlers.
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
from ..Constants.constants import splinker_logger, HANDLER_MAP
from oaLogging.Methods.matrix_gate import matrix_log, is_debug_allowed

def _is_debug():
    return is_debug_allowed(system="CORE", element="SPLINKER")

class SplinkPipeline:
    def __init__(self, splink, splinker_manager):
        self.splink = splink
        self.splinker_manager = splinker_manager
        self.handlers = []
        self._build_pipeline()

    def _build_pipeline(self):
        handler_configs = self.splink.get("handlers", [])
        matrix_log("core", "splinker", "_build_pipeline", 
                   f"🛠️ SplinkPipeline: Building pipeline for {self.splink['id']} with {len(handler_configs)} handler configs.", "DEBUG")

        for config in handler_configs:
            if not config.get("enabled", False): 
                matrix_log("core", "splinker", "_build_pipeline", 
                           f"  ⏭️ Handler {config.get('type')} is DISABLED. Skipping.", "DEBUG")
                continue
            
            handler_class = HANDLER_MAP.get(config["type"])
            if handler_class:
                self.handlers.append(handler_class(config.get("params", {})))
                matrix_log("core", "splinker", "_build_pipeline", f"  ✅ Loaded handler: {config['type']}", "DEBUG")
            else:
                log_msg = f"Unknown handler type: {config['type']}"
                matrix_log("core", "splinker", "_build_pipeline", log_msg, "WARNING")
                self.splinker_manager._notify_monitor("debug_log", log_msg)

        matrix_log("core", "splinker", "_build_pipeline", 
                   f"🛠️ SplinkPipeline: Pipeline for {self.splink['id']} complete. Active handlers: {len(self.handlers)}", "DEBUG")


    def process(self, value, state, direction="FORWARD"):
        src = self.splink.get("source", "Unknown")
        dest = self.splink.get("dest", "Unknown")
        label = self.splink.get("label", "Splink")
        
        # ⚡ OPTIMIZATION: Only track transformation steps if debugging is enabled
        event_data = None
        if _is_debug():
            event_data = {
                "ts": time.time(),
                "splink_id": self.splink["id"],
                "label": label,
                "direction": direction,
                "source": src,
                "dest": dest,
                "input_val": value,
                "steps": [],
                "msg_guid": state.get("msg_guid", "UNKNOWN"),
                "msg_type": state.get("msg_type", "LINK_FEEDBACK"),
                "origin_source": state.get("origin_source", "UNKNOWN"),
                "guid": f"{state.get('original_guid', 'UNKNOWN')}-SPLINK",
                "orig_guid": state.get("original_guid"),
                "orig_ts": state.get("original_ts")
            }

        for handler in self.handlers:
            handler_name = handler.__class__.__name__
            new_value = handler.execute(value, self.splink, state, direction=direction)
            
            if event_data:
                event_data["steps"].append({
                    "handler": handler_name,
                    "in": value,
                    "out": new_value
                })

            if new_value is None:
                if event_data:
                    log_msg = f"🛑 {label} [{self.splink['id']}] Terminated by {handler_name}."
                    matrix_log("core", "splinker", "process", log_msg, "DEBUG")
                    event_data["terminated_by"] = handler_name
                    self.splinker_manager._notify_monitor("splink_event", event_data)
                return None
            value = new_value
        
        if event_data:
            event_data["output_val"] = value
            log_msg = f"🔗 {label} [{self.splink['id']}] {direction}: {src} ➔ {dest} | {value}"
            matrix_log("core", "splinker", "process", log_msg, "DEBUG")
            self.splinker_manager._notify_monitor("splink_event", event_data)

        return value
