from ..manager_constants import Splinker_debug_enabled, splinker_logger

def _broker_splice(self, splink, val, original_source, original_msg=None):
    if not self.state_cache_manager: return
    dest_topic, dest_key = self._parse_splink_path(splink["dest"])
    
    if not dest_topic: return
    
    target_val = val
    if dest_key:
        # We need to inject 'val' into the existing dict at 'dest_topic'
        current_dict = self.state_cache_manager.get(dest_topic)
        if not isinstance(current_dict, dict):
            current_dict = {}
        new_dict = current_dict.copy()
        new_dict[dest_key] = val
        target_val = new_dict
        
    cached_val = self.state_cache_manager.get(dest_topic)
    if cached_val == target_val: return
    
    if Splinker_debug_enabled:
        splinker_logger.info(f"🔗 Splinker: SPLICE [{splink['id']}] Brokering {original_source} -> {dest_topic} value={target_val}")

    # ⚡ ANTI-FEEDBACK SPEC: Brokered messages are LINK_FEEDBACK
    meta = {
        "msg_type": "LINK_FEEDBACK",
        "is_settled": False,
        "splink_id": splink["id"],
        "splinker_source": splink["id"],
        "splink_active": True,
        "splink_source_path": splink["source"],
        "splink_dest_path": splink["dest"],
        "splink_label": splink.get("label", "Splink")
    }
    
    if original_msg:
        orig_guid = original_msg.get("msg_guid") or original_msg.get("logical_guid") or original_msg.get("guid")
        orig_source = original_msg.get("origin_source") or original_source
        orig_ts = original_msg.get("ts")
        
        # ⚡ ANTI-FEEDBACK SPEC: Preserve the original GUID and Source
        meta["msg_guid"] = orig_guid
        meta["origin_source"] = orig_source
        
        # Store derivation context
        meta["orig_guid"] = orig_guid
        meta["orig_ts"] = orig_ts
        
        # Legacy GUID support
        meta["GUID"] = f"{orig_guid}-SPLINK"
        meta["ts"] = orig_ts

    self.state_cache_manager.handle_external_update(dest_topic, target_val, source="SPLINKER", metadata=meta)
