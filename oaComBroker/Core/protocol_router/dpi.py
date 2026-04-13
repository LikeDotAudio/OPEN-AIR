# Core/protocol_router/dpi.py
#
# Deep Packet Inspection (DPI) and Message Enrichment for the Protocol Router.
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
# Version 20260328.1440.1
#
# Description:
# This module implements the forensic "investigation" phase of the ProtocolRouter
# pipeline. It performs Deep Packet Inspection to extract protocol-specific 
# details, resolve OIDs, and flag safety-critical hardware mutations.
#
# Architectural Role:
# - Enriches the Unified Message Schema with forensic metadata.
# - Decouples protocol-specific dissection from the core routing logic.
# - Identifies anomalous payloads (Blobs) and critical control signals (YAK).

def investigate_packet(message, mib_cache=None):
    """
    Executes Deep Packet Inspection to enrich message metadata.
    
    This function analyzes the topic and transport source to apply protocol-
    specific forensic tags. It modifies the 'meta' dictionary of the 
    provided message in-place.
    
    Args:
        message (dict): The normalized message packet to investigate.
        mib_cache (dict, optional): A cache for SNMP OID-to-Name resolution.
        
    Side Effects:
        - Modifies message["meta"] by adding 'investigation', 'mib_resolution', 
          'blob', or 'mutation' keys.
    """
    topic = str(message["topic"])
    source = message["source"]
    
    # --- SNMP Investigation: Resolve numeric OIDs to human-readable names ---
    if source == "SNMP" or topic.startswith(".1.3.6"):
        mib = mib_cache.get(topic, "Unknown OID") if mib_cache else "Unknown OID"
        message["meta"]["mib_resolution"] = mib
        message["meta"]["investigation"] = f"SNMP MIB: {mib}"
        
    # --- OSC Investigation: Map logical topics back to OSC addresses ---
    if source == "OSC" or "osc_address" in message["meta"]:
        osc_addr = message["meta"].get("osc_address", 
                                   "/" + topic.replace("OPEN-AIR/", ""))
        message["meta"]["investigation"] = f"OSC Map: {osc_addr}"

    # --- MIDI Investigation: Dissect raw bytes and identify signal type ---
    if source == "MIDI" or "midi_raw" in message["meta"]:
        raw = message["meta"].get("midi_raw", "Unknown Message")
        port = message["meta"].get("midi_port", "Remote")
        m_type = message["meta"].get("midi_type", "message")
        
        # Flag real-time clock signals to differentiate from control changes.
        if "clock" in raw.lower():
            message["meta"]["investigation"] = f"🎹 MIDI [CLOCK] from {port}"
        else:
            message["meta"]["investigation"] = f"🎹 MIDI [{m_type.upper()}] " \
                                            f"from {port}"

    # --- YAK Hardware Safety: Flag potential hardware mutations ---
    # Mutation events (SET, NAB) require elevated logging and audit trails.
    if "YAK" in topic.upper():
        if any(k in topic.upper() for k in ["SET", "NAB", "LEVEL", "FREQ"]):
            message["meta"]["mutation"] = True
            message["meta"]["investigation"] = "🚨 YAK Hardware Mutation"

    # --- Splink Investigation: Trace brokered relationships ---
    if message["meta"].get("splink_active"):
        s_id = message["meta"].get("splink_id", "Link")
        s_dest = message["meta"].get("splink_dest", "Destination")
        message["meta"]["investigation"] = f"🔗 Splink Sync [{s_id}] ➜ {s_dest}"

    # --- Data Volume Check: Detect oversized configuration blobs ---
    val_str = str(message["value"])
    if len(val_str) > 1000:
        message["meta"]["blob"] = True
        message["meta"]["investigation"] = f"📦 Large Configuration Blob " \
                                        f"({len(val_str)} bytes)"
