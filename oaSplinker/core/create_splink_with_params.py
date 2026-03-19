import time
from ..pipeline import SplinkPipeline
from ..constants import Splinker_debug_enabled, splinker_logger

def create_splink_with_params(self, source, dest, source_val=None, dest_val=None):
    splinker_logger.info(f"🔗 Splinker: create_splink_with_params received. Source={source} ({source_val}), Dest={dest} ({dest_val})")
    if not source or not dest:
        splinker_logger.error(f"❌ Splinker: Cannot create splink with missing source or dest. source={source}, dest={dest}")
        return None

    # ⚡ ROBUSTNESS: Ensure source and dest are strings for split()
    src_label = str(source).split('/')[-1] if source else "UNKNOWN"
    dest_label = str(dest).split('/')[-1] if dest else "UNKNOWN"

    new_id = f"SPLINK_{int(time.time() * 1000)}"
    
    # ⚡ UNIQUE PREVENTION: Avoid duplicate splinks for the same source/dest pair
    for s in self.splinks:
        if s.get("source") == source and s.get("dest") == dest:
            if Splinker_debug_enabled:
                splinker_logger.debug(f"  ⏭️ Splink already exists for {source} -> {dest}. Skipping duplicate.")
            return s["id"]

    # Create with a default scale handler as requested (MIN/MAX source -> MIN/MAX dest)
    splink = {
        "id": new_id, 
        "source": source, 
        "dest": dest, 
        "mode": "SPLINK",
        "active": True, 
        "label": f"Splink: {src_label} -> {dest_label}", 
        "handlers": [
            {
                "type": "scale",
                "enabled": True,
                "params": {
                    "source_min": 0,
                    "source_max": 127,
                    "dest_min": 0,
                    "dest_max": 100
                }
            }
        ]
    }
    self.splinks.append(splink)
    self._save_splink(splink)
    
    # Detailed Debug Report for Discovery
    debug_report = [
        f"╔════════════ DIRECT SPLINK DISCOVERY ════════════╗",
        f"  ID         : {new_id}",
        f"  SOURCE     : {source}",
        f"  DEST       : {dest}",
        f"  MODE       : SPLINK (Bidirectional)",
        f"  HANDLERS   : [Scale] 0-127 -> 0-100 (Default)"
    ]

    # ⚡ STATE CONNECTION: Trigger an immediate sync from source to dest
    # Priority: 1. Observed value from UI, 2. Current value from Cache
    current_val = source_val
    sync_method = "Investigation (Live)"
    
    if current_val is None and self.state_cache_manager:
        src_topic, src_key = self._parse_splink_path(source)
        current_val = self.state_cache_manager.get(src_topic)
        sync_method = "System Cache (Warm)"

    if current_val is not None:
        # We process it through the pipeline
        pipeline = SplinkPipeline(splink, self)
        processed = pipeline.process(current_val, {}, direction="FORWARD")
        
        debug_report.append(f"  SYNC ({sync_method}): {current_val} -> {processed} (Linkage Point)")
        
        if processed is not None:
            self._broker_splice(splink, processed, "GUI-INIT")
    else:
        debug_report.append(f"  SYNC       : No source state found. Waiting for movement.")

    debug_report.append(f"╚══════════════════════════════════════════════════╝")
    
    full_debug = "\n".join(debug_report)

    # ⚡ FIREHOSE: Ingest creation event for visibility
    from oaComBroker.protocol_router import ProtocolRouter
    ProtocolRouter.get_instance().ingest("SPLINKER", f"OPEN-AIR/System/Status/Splinker/{new_id}", "CREATED", {"id": new_id, "type": "Direct", "source": source, "dest": dest})

    if Splinker_debug_enabled:
        splinker_logger.info(f"🔗 Splinker: create_splink_with_params(source='{source}', dest='{dest}') CALL received.")
        splinker_logger.info(f"🔗 Splinker: Direct Splink Created {new_id}")
        self._notify_monitor("debug_log", full_debug)
