# Core/broker_splice.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from ..Constants.constants import Splinker_debug_enabled, splinker_logger


def broker_splice(self, splink, value, original_source, original_message=None):
    if not self.state_cache_manager: return
    dest_topic, dest_key = self.parse_splink_path(splink["dest"])

    if not dest_topic: return

    target_val = value
    if dest_key:
        # We need to inject 'value' into the existing dict at 'dest_topic'
        current_dict = self.state_cache_manager.get(dest_topic)
        if not isinstance(current_dict, dict):
            current_dict = {}
        new_dict = current_dict.copy()
        new_dict[dest_key] = value
        target_val = new_dict

    cached_val = self.state_cache_manager.get(dest_topic)
    if cached_val == target_val: return

    if Splinker_debug_enabled:
        splinker_logger.info(f"🔗 Splinker: SPLICE [{splink['id']}] Brokering {original_source} -> {dest_topic} value={target_val}")

    # ⚡ ANTI-FEEDBACK SPEC: Brokered messages are LINK_FEEDBACK
    meta = {
        "message_type": "LINK_FEEDBACK",
        "is_settled": False,
        "splink_id": splink["id"],
        "splinker_source": splink["id"],
        "splink_active": True,
        "splink_source_path": splink["source"],
        "splink_dest_path": splink["dest"],
        "splink_label": splink.get("label", "Splink")
    }

    if original_message:
        orig_guid = original_message.get("message_guid") or original_message.get("logical_guid") or original_message.get("guid")
        orig_source = original_message.get("origin_source") or original_source
        orig_ts = original_message.get("timestamp")

        # ⚡ ANTI-FEEDBACK SPEC: Preserve the original GUID and Source
        meta["message_guid"] = orig_guid
        meta["origin_source"] = orig_source

        # Store derivation context
        meta["orig_guid"] = orig_guid
        meta["orig_ts"] = orig_ts

        # Legacy GUID support
        meta["GUID"] = f"{orig_guid}-SPLINK"
        meta["timestamp"] = orig_ts

    self.state_cache_manager.handle_external_update(dest_topic, target_val, source="SPLINKER", metadata=meta)
