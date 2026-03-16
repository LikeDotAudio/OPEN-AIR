from ..constants import Splinker_debug_enabled, splinker_logger

def broker_link(self, splink, val, original_source, original_msg=None):
    if not self.state_cache_manager: return
    src_topic, src_key = self.parse_splink_path(splink["source"])
    
    if not src_topic: return
    
    target_val = val
    if src_key:
        current_dict = self.state_cache_manager.get(src_topic)
        if not isinstance(current_dict, dict):
            current_dict = {}
        new_dict = current_dict.copy()
        new_dict[src_key] = val
        target_val = new_dict
        
    cached_val = self.state_cache_manager.get(src_topic)
    if cached_val == target_val: return
    
    if Splinker_debug_enabled:
        splinker_logger.info(f"🔗 Splinker: LINK [{splink['id']}] Brokering {original_source} -> {src_topic} value={target_val}")

    # ⚡ ANTI-FEEDBACK SPEC: Brokered messages are LINK_FEEDBACK
    meta = {
        "msg_type": "LINK_FEEDBACK",
        "is_settled": False,
        "splink_id": splink["id"],
        "splinker_source": splink["id"],
        "splink_active": True,
        "splink_source_path": splink["dest"], # REVERSE: Dest is the trigger
        "splink_dest_path": splink["source"], # REVERSE: Source is the destination
        "splink_label": splink.get("label", "Splink (REVERSE)")
    }
    
    if original_msg:
        orig_guid = original_msg.get("msg_guid") or original_msg.get("logical_guid") or original_msg.get("guid")
        orig_source = original_msg.get("origin_source") or original_source
        orig_ts = original_msg.get("ts")
        
        # ⚡ ANTI-FEEDBACK SPEC: Preserve original Identity
        meta["msg_guid"] = orig_guid
        meta["origin_source"] = orig_source
        
        # Store derivation context
        meta["orig_guid"] = orig_guid
        meta["orig_ts"] = orig_ts
        
        # Legacy GUID support
        meta["GUID"] = f"{orig_guid}-SPLINK"
        meta["ts"] = orig_ts

    self.state_cache_manager.handle_external_update(src_topic, target_val, source="SPLINKER", metadata=meta)
