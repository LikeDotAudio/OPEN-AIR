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

import random
import time

from oaLogging.Methods.matrix_gate import matrix_log

from .constants import app_constants


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
    rust_router=None,
    is_active=True
):
    # ⚡ HUB-AND-SPOKE: Ingress Gate
    # Access the ProtocolRouter singleton to check if this source is permitted
    from oaComBroker.Core.protocol_router.manager import ProtocolRouter
    router = ProtocolRouter.get_instance()
    if not router.ingest_enabled.get(transport_source, True):
        return None # Silently drop traffic from disabled protocols

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
        is_active (bool, optional): Whether this instance is the primary broker.

        
    Side Effects:
        - May drop packets due to dead-band or interaction locks.
        - Injects a new dictionary into the inbound_queue.
    """
    val_str = str(value)[:100] + ("..." if len(str(value)) > 100 else "")
    if app_constants.ROUTER_INGEST_LOGS:
        matrix_log("comms", "broker", "normalize_and_ingest", f"📡📥📥 [INBOUND] {transport_source} on {topic}: {val_str}", "DEBUG")


    # Standardize None to empty string or keep as None depending on protocol?
    # For OPEN-AIR, None is a valid 'Reset' state for many parameters,
    # but we must ensure it doesn't crash consumers.
    if value is None:
        if app_constants.ROUTER_INGEST_LOGS:
            matrix_log("comms", "broker", "normalize_and_ingest", f"⚠️ [ROUTER] Received 'None' for {topic}. Propagating as Reset state.", "TRACE")
        return

    meta = metadata or {}

    # --- STATE DELTA CHECK (Loop Prevention / Noise Reduction) ---
    # ⚡ EXCEPTION: Monitor, Firehose, and MIDI topics are event streams.
    # They must never be dropped by dead-band logic.
    is_event_stream = any(x in str(topic) for x in ["/Monitor/", "/Firehose/", "/MIDI/"])

    if state_cache and not meta.get("boot") and not is_event_stream:
        cached_val = state_cache.get_cached_value(topic)
        if cached_val == value:
            if app_constants.ROUTER_INGEST_LOGS:
                matrix_log("comms", "broker", "normalize_and_ingest", f"📉🚫📉 [ROUTER] DEAD-BAND: Dropping identical value for {topic}", "TRACE")
            return

    # Boot sequence messages are ingested silently to prevent console flood.
    if meta.get("boot"):
        if app_constants.ROUTER_INGEST_LOGS:
            matrix_log("comms", "broker", "normalize_and_ingest", f"👢🤫👢 [BOOT] Silent ingestion for {topic}", "DEBUG")
        silent_ingest_callback(transport_source, topic, value, meta)
        return

    # --- Identity Extraction & Loop Prevention ---
    session_guid = meta.get("GUID") or meta.get("guid") or local_guid
    partition = meta.get("partition") or app_constants.PARTITION_ID
    full_id = meta.get("full_id") or app_constants.FULL_INSTANCE_ID

    logical_source = transport_source

    # ⚡ PROTOCOL AUTO-DETECTION:
    # If the transport is MQTT, we check the topic prefix to see if it belongs
    # to a specific logical protocol partition (GUI, MIDI, etc.)
    if transport_source == "MQTT":
        from .router import ProtocolRouter
        p_prefixes = ProtocolRouter.get_instance().protocol_prefixes
        for p_name, prefix in p_prefixes.items():
            # Support both single prefix string and list of prefixes
            prefixes = [prefix] if isinstance(prefix, str) else prefix
            if any(str(topic).startswith(p) for p in prefixes):
                logical_source = p_name
                break

    # --- V3.1.5 TOPIC SANITIZATION (AGGRESSIVE) ---
    # Prevent recursive protocol prefixing (e.g., OPEN-AIR/OSC/OSC/OSC/...)
    # This logic identifies repeated protocol tokens and collapses them.
    if any(x + "/" + x + "/" in str(topic) for x in ["OSC", "MIDI", "GUI", "oaGui"]):
        parts = str(topic).split("/")
        unique_parts = []
        for p in parts:
            if p in ["OSC", "MIDI", "GUI", "oaGui"] and unique_parts and unique_parts[-1] == p:
                continue
            unique_parts.append(p)
        topic = "/".join(unique_parts)

    logical_guid = session_guid

    id_src = meta.get("source") or meta.get("logical_source")
    id_guid = meta.get("guid") or meta.get("logical_guid")

    if isinstance(value, dict):
        id_src = id_src or value.get("source") or value.get("logical_source")
        id_guid = id_guid or value.get("guid") or value.get("logical_guid")

    if id_src: logical_source = str(id_src).upper()
    if id_guid: logical_guid = id_guid

    # --- Unified Message Schema Extraction ---
    message_guid = meta.get("message_guid")
    message_type = meta.get("message_type")
    origin_source = meta.get("origin_source")
    is_settled = meta.get("is_settled")

    if isinstance(value, dict):
        message_guid = message_guid or value.get("message_guid")
        message_type = message_type or value.get("message_type")
        origin_source = origin_source or value.get("origin_source")
        if is_settled is None:
            is_settled = value.get("is_settled")

    message_guid = (message_guid or meta.get("GUID") or
               f"G-{int(time.time()*1000)}-{random.getrandbits(16)}")
    message_type = (message_type or "SPLICE_ACTION").upper()
    origin_source = origin_source or logical_source
    if is_settled is None:
        is_settled = False

    # --- V3.0.0 METADATA HARDENING ---
    # Ensure 'src' (Source Identity) is explicitly tagged for Echo Cancellation.
    # If not provided by transport, we inject the local full_id.
    message_src_id = meta.get("src")
    if isinstance(value, dict):
        message_src_id = message_src_id or value.get("src")

    message_src_id = message_src_id or full_id

    # ⚡ V3.1.16 REFLECTION IDENTIFICATION
    is_reflection = meta.get("is_reflection") or (message_src_id == full_id and transport_source == "MQTT")

    if is_reflection:
        if app_constants.ROUTER_INGEST_LOGS:
            matrix_log("comms", "broker", "normalize_and_ingest", f"🛡️ [ECHO] Reflection identified for {topic} (Src: {message_src_id})", "TRACE")

    # INTERACTION LOCK (BROKER LEVEL):
    # Prevents self-reflection loops when a parameter is actively being
    # modified by a user on this instance.
    if message_type == "LINK_FEEDBACK":
        if settle_manager.is_parameter_locked(topic, full_id):
            if app_constants.ROUTER_INGEST_LOGS:
                matrix_log("comms", "broker", "normalize_and_ingest", f"🔒🚫🔒 [ROUTER] BLOCKADE: Rejecting self-reflection for locked parameter {topic}", "TRACE")
            return

    # Final Normalized Packet Construction.
    message = {
        "timestamp": time.time(),
        "source": transport_source,
        "logical_source": logical_source,
        "topic": topic,
        "value": value,
        "meta": meta,
        "guid": session_guid,
        "full_id": full_id,
        "logical_guid": logical_guid,
        "partition": partition,
        "message_guid": message_guid,
        "message_type": message_type,
        "origin_source": origin_source,
        "is_settled": is_settled,
        "src": message_src_id,
        "is_reflection": is_reflection
    }

    # Update metadata dictionary for downstream consumers.
    meta.update({
        "message_guid": message_guid,
        "message_type": message_type,
        "origin_source": origin_source,
        "is_settled": is_settled,
        "full_id": full_id,
        "src": message_src_id,
        "is_reflection": is_reflection
    })

    inbound_queue.put(message)

    # ⚡ RUST NATIVE ACCELERATION: Push to Rust router for high-speed numeric paths
    # TODO: BUG: The rust_router integration causes the ingest pipeline to hang.
    # Disabling until the Rust component can be fixed.
    # if rust_router:
    #     rust_router.push_inbound(message)

    # TERMINAL SETTLING:
    # If this is a primary action, lock the parameter and schedule a
    # settling event to confirm final state.
    # ⚡ EXCEPTION: Command topics (/Control/), Telemetry (/Status/),
    # Event Streams (/MIDI/), and Failover (/Failover/) represent transient events.
    # They must NOT be settled to prevent recursive feedback loops.
    is_settleable = not any(x in str(topic) for x in ["/Control/", "/Status/", "/MIDI/", "/Failover/"])

    # ⚡ SHADOW GATING:
    # Only the active broker (PRIMARY) settles messages arriving from MQTT.
    # This ensures that only one instance in a failover group issues the
    # final LINK_FEEDBACK for external commands.
    # Non-MQTT sources (hardware, local UI) are always settled by the local
    # broker that received them.
    should_settle = (message_type == "SPLICE_ACTION" and is_settleable and not is_settled)
    if should_settle:
        is_mqtt = (transport_source == "MQTT")

        if not is_mqtt or (is_mqtt and is_active):
            settle_manager.lock_parameter(topic, full_id)
            settle_manager.schedule_settling(topic, message)

def create_silent_message(transport_source, topic, value, meta, local_guid, rust_router=None):
    """
    Internal helper for low-priority/boot ingestion.
    
    Allocates a pre-settled message that bypasses the normal processing loops.
    """
    message = {
        "timestamp": time.time(), "source": transport_source, "topic": topic,
        "value": value, "meta": meta, "guid": local_guid,
        "partition": app_constants.PARTITION_ID,
        "full_id": app_constants.FULL_INSTANCE_ID,
        "message_type": "LINK_FEEDBACK", "is_settled": True
    }

    # TODO: BUG: The rust_router integration causes the ingest pipeline to hang.
    # if rust_router:
    #     rust_router.push_inbound(message)

    return message
