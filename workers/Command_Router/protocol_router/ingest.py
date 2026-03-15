# workers/Command_Router/protocol_router/ingest.py
#
# Logic for data normalization and unified message schema creation.

import time
import random
from .constants import LOCAL_DEBUG, app_constants
from workers.logger.logger import router_logger

def normalize_and_ingest(
    transport_source, 
    topic, 
    value, 
    metadata, 
    local_guid, 
    settle_manager, 
    inbound_queue,
    silent_ingest_callback
):
    """
    Normalizes raw data into the Unified Message Schema and appends to queue.
    """
    val_str = str(value)[:100] + ("..." if len(str(value)) > 100 else "")
    router_logger.debug(f"📡📥📥 [INBOUND] {transport_source} on {topic}: {val_str}")
        
    # Ignore traffic intended for the router's own monitoring topics.
    if any(x in str(topic) for x in ["/System/Router/", "/Firehose/"]):
        return

    meta = metadata or {}
    
    # Boot sequence messages are ingested silently.
    if meta.get("boot"):
        if LOCAL_DEBUG:
            router_logger.debug(f"👢🤫👢 [BOOT] Silent ingestion for {topic}")
        silent_ingest_callback(transport_source, topic, value, meta)
        return

    # Identity extraction for loop prevention.
    session_guid = meta.get("GUID") or meta.get("guid") or local_guid
    partition = meta.get("partition") or app_constants.PARTITION_ID
    full_id = meta.get("full_id") or app_constants.FULL_INSTANCE_ID
    
    logical_source = transport_source
    logical_guid = session_guid
    
    id_src = meta.get("source") or meta.get("logical_source")
    id_guid = meta.get("guid") or meta.get("logical_guid")
    
    if isinstance(value, dict):
        id_src = id_src or value.get("source") or value.get("logical_source")
        id_guid = id_guid or value.get("guid") or value.get("logical_guid")
        
    if id_src: logical_source = str(id_src).upper()
    if id_guid: logical_guid = id_guid
    
    # Unified Message Schema extraction.
    msg_guid = meta.get("msg_guid")
    msg_type = meta.get("msg_type")
    origin_source = meta.get("origin_source")
    is_settled = meta.get("is_settled")
    
    if isinstance(value, dict):
        msg_guid = msg_guid or value.get("msg_guid")
        msg_type = msg_type or value.get("msg_type")
        origin_source = origin_source or value.get("origin_source")
        if is_settled is None:
            is_settled = value.get("is_settled")

    msg_guid = (msg_guid or meta.get("GUID") or 
               f"G-{int(time.time()*1000)}-{random.getrandbits(16)}")
    msg_type = (msg_type or "SPLICE_ACTION").upper()
    origin_source = origin_source or logical_source
    if is_settled is None:
        is_settled = False
    
    # INTERACTION LOCK (BROKER LEVEL): 
    if msg_type == "LINK_FEEDBACK":
        if settle_manager.is_parameter_locked(topic, full_id):
            if LOCAL_DEBUG:
                router_logger.trace(
                    f"🔒🚫🔒 [ROUTER] BLOCKADE: Rejecting self-"
                    f"reflection for locked parameter {topic}"
                )
            return

    msg = {
        "ts": time.time(),
        "source": transport_source,
        "logical_source": logical_source,
        "topic": topic,
        "val": value,
        "meta": meta,
        "guid": session_guid,
        "full_id": full_id,
        "logical_guid": logical_guid,
        "partition": partition,
        "msg_guid": msg_guid,
        "msg_type": msg_type,
        "origin_source": origin_source,
        "is_settled": is_settled
    }
    
    meta.update({
        "msg_guid": msg_guid,
        "msg_type": msg_type,
        "origin_source": origin_source,
        "is_settled": is_settled,
        "full_id": full_id
    })
    
    inbound_queue.put(msg)
    
    # TERMINAL SETTLING:
    if msg_type == "SPLICE_ACTION":
        settle_manager.lock_parameter(topic, full_id)
        settle_manager.schedule_settling(topic, msg)

def create_silent_msg(transport_source, topic, value, meta, local_guid):
    """Internal helper for low-priority/boot ingestion."""
    return {
        "ts": time.time(), "source": transport_source, "topic": topic,
        "val": value, "meta": meta, "guid": local_guid,
        "partition": app_constants.PARTITION_ID,
        "full_id": app_constants.FULL_INSTANCE_ID,
        "msg_type": "LINK_FEEDBACK", "is_settled": True
    }
