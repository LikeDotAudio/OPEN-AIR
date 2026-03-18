import time
from .constants import Splinker_debug_enabled, splinker_logger, HANDLER_MAP

class SplinkPipeline:
    def __init__(self, splink, splinker_manager):
        self.splink = splink
        self.splinker_manager = splinker_manager
        self.handlers = []
        self._build_pipeline()

    def _build_pipeline(self):
        handler_configs = self.splink.get("handlers", [])
        if Splinker_debug_enabled:
            splinker_logger.debug(f"🛠️ SplinkPipeline: Building pipeline for {self.splink['id']} with {len(handler_configs)} handler configs.")

        for config in handler_configs:
            if not config.get("enabled", False): 
                if Splinker_debug_enabled:
                    splinker_logger.debug(f"  ⏭️ Handler {config.get('type')} is DISABLED. Skipping.")
                continue
            
            handler_class = HANDLER_MAP.get(config["type"])
            if handler_class:
                self.handlers.append(handler_class(config.get("params", {})))
                if Splinker_debug_enabled:
                    splinker_logger.debug(f"  ✅ Loaded handler: {config['type']}")
            elif Splinker_debug_enabled:
                log_msg = f"Unknown handler type: {config['type']}"
                splinker_logger.warning(log_msg)
                self.splinker_manager._notify_monitor("debug_log", log_msg)

        if Splinker_debug_enabled:
            splinker_logger.debug(f"🛠️ SplinkPipeline: Pipeline for {self.splink['id']} complete. Active handlers: {len(self.handlers)}")


    def process(self, value, state, direction="FORWARD"):
        original_value = value
        src = self.splink.get("source", "Unknown")
        dest = self.splink.get("dest", "Unknown")
        label = self.splink.get("label", "Splink")
        
        # ⚡ STRUCTURED LOGGING: Track transformation steps
        event_data = {
            "ts": time.time(),
            "splink_id": self.splink["id"],
            "label": label,
            "direction": direction,
            "source": src,
            "dest": dest,
            "input_val": value,
            "steps": [],
            # ⚡ IDENTITY: Carry over Spec fields for the report
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
            
            # Record step
            event_data["steps"].append({
                "handler": handler_name,
                "in": value,
                "out": new_value
            })

            if new_value is None:
                if Splinker_debug_enabled:
                    log_msg = f"🛑 {label} [{self.splink['id']}] Terminated by {handler_name}."
                    splinker_logger.debug(log_msg)
                    event_data["terminated_by"] = handler_name
                    self.splinker_manager._notify_monitor("splink_event", event_data)
                return None
            value = new_value
        
        event_data["output_val"] = value
        if Splinker_debug_enabled:
            # Still log to disk for forensics
            log_msg = f"🔗 {label} [{self.splink['id']}] {direction}: {src} ➔ {dest} | {value}"
            splinker_logger.debug(log_msg)
            # Notify UI with structured data
            self.splinker_manager._notify_monitor("splink_event", event_data)

        return value
