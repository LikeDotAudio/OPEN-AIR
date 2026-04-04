# Core/protocol_router/ingest.py
#
# Logic for data normalization and unified message schema creation.
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
# Version 20260328.1420.1
#
# Description:
# This module implements the ingestion and normalization phase of the 
# ProtocolRouter. It transforms raw transport-specific data into a strict,
# logically consistent "Unified Message Schema." This ensures that downstream
# components (DPI, Strategy, Dispatch) can operate on a predictable data 
# structure regardless of the original protocol.
#
# Architectural Role:
# - Acts as the primary ingress point for all communication traffic.
# - Implements Dead-Band filtering to reduce redundant network noise.
# - Manages "Interaction Locks" to prevent feedback loops during user input.
# - Enforces session identity and partition isolation.

import time
import random
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Methods.matrix_gate import matrix_log

def normalize_and_ingest(
    transport_source, 
    topic, 
    value, 
    metadata, 
    local_guid, 
    settle_manager, 
    inbound_queue,
    silent_ingest_callback,
    state_cache=None,
    rust_router=None
):
    """
    Normalizes raw data into the Unified Message Schema and appends to queue.

    Args:
        transport_source (str): Origin (e.g., 'MQTT', 'OSC', 'MIDI').
        topic (str): The logical address or key.
        value (any): The payload.
        metadata (dict): Contextual headers from the transport layer.
        local_guid (str): GUID of the local router instance.
        settle_manager (SettleManager): Reference to the settling engine.
        inbound_queue (Queue): Target queue for processed messages.
        silent_ingest_callback (fn): Handler for boot-time traffic.
        state_cache (Cache, optional): Global state for dead-band checks.
        rust_router (CoreRouter, optional): High-performance Rust router.

        
    Side Effects:
        - May drop packets due to dead-band or interaction locks.
        - Injects a new dictionary into the inbound_queue.
    """
    val_str = str(value)[:100] + ("..." if len(str(value)) > 100 else "")
    matrix_log("core", "router", "normalize_and_ingest", f"📡📥📥 [INBOUND] {transport_source} on {topic}: {val_str}", "DEBUG")
        
    # Standardize None to empty string or keep as None depending on protocol?
    # For OPEN-AIR, None is a valid 'Reset' state for many parameters, 
    # but we must ensure it doesn't crash consumers.
    if value is None:
        matrix_log("core", "router", "normalize_and_ingest", f"⚠️ [ROUTER] Received 'None' for {topic}. Propagating as Reset state.", "TRACE")
    if any(x in str(topic) for x in ["/System/Router/", "/Firehose/"]):
        return

    meta = metadata or {}

    # --- STATE DELTA CHECK (Loop Prevention / Noise Reduction) ---
    # ⚡ EXCEPTION: Monitor, Firehose, and MIDI topics are event streams.
    # They must never be dropped by dead-band logic.
    is_event_stream = any(x in str(topic) for x in ["/Monitor/", "/Firehose/", "/MIDI/"])
    
    if state_cache and not meta.get("boot") and not is_event_stream:
        cached_val = state_cache.get_cached_value(topic)
        if cached_val == value:
            matrix_log("core", "router", "normalize_and_ingest", f"📉🚫📉 [ROUTER] DEAD-BAND: Dropping identical value for {topic}", "TRACE")
            return
    
    # Boot sequence messages are ingested silently to prevent console flood.
    if meta.get("boot"):
        matrix_log("core", "router", "normalize_and_ingest", f"👢🤫👢 [BOOT] Silent ingestion for {topic}", "DEBUG")
        silent_ingest_callback(transport_source, topic, value, meta)
        return

    # --- Identity Extraction & Loop Prevention ---
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
    
    # --- Unified Message Schema Extraction ---
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
    # Prevents self-reflection loops when a parameter is actively being 
    # modified by a user on this instance.
    if msg_type == "LINK_FEEDBACK":
        if settle_manager.is_parameter_locked(topic, full_id):
            matrix_log("core", "router", "normalize_and_ingest", f"🔒🚫🔒 [ROUTER] BLOCKADE: Rejecting self-reflection for locked parameter {topic}", "TRACE")
            return

    # Final Normalized Packet Construction.
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
    
    # Update metadata dictionary for downstream consumers.
    meta.update({
        "msg_guid": msg_guid,
        "msg_type": msg_type,
        "origin_source": origin_source,
        "is_settled": is_settled,
        "full_id": full_id
    })
    
    inbound_queue.put(msg)
    
    # ⚡ RUST NATIVE ACCELERATION: Push to Rust router for high-speed numeric paths
    if rust_router:
        rust_router.push_inbound(msg)
    
    # TERMINAL SETTLING:
    # If this is a primary action, lock the parameter and schedule a 
    # settling event to confirm final state.
    # ⚡ EXCEPTION: Command topics (/Control/) and Telemetry (/Status/)
    # represent transient events or periodic heartbeats. They must NOT
    # be settled to prevent recursive feedback loops.
    is_settleable = not any(x in str(topic) for x in ["/Control/", "/Status/"])
    
    if msg_type == "SPLICE_ACTION" and is_settleable:
        settle_manager.lock_parameter(topic, full_id)
        settle_manager.schedule_settling(topic, msg)

def create_silent_msg(transport_source, topic, value, meta, local_guid, rust_router=None):
    """
    Internal helper for low-priority/boot ingestion.
    
    Allocates a pre-settled message that bypasses the normal processing loops.
    """
    msg = {
        "ts": time.time(), "source": transport_source, "topic": topic,
        "val": value, "meta": meta, "guid": local_guid,
        "partition": app_constants.PARTITION_ID,
        "full_id": app_constants.FULL_INSTANCE_ID,
        "msg_type": "LINK_FEEDBACK", "is_settled": True
    }
    
    if rust_router:
        rust_router.push_inbound(msg)
        
    return msg
