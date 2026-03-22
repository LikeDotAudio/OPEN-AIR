# protocol_router/dpi.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Deep Packet Inspection (DPI) and Message Enrichment.

def investigate_packet(msg, mib_cache=None):
    """
    Executes Deep Packet Inspection to enrich message metadata.
    """
    topic = str(msg["topic"])
    source = msg["source"]
    
    if source == "SNMP" or topic.startswith(".1.3.6"):
        mib = mib_cache.get(topic, "Unknown OID") if mib_cache else "Unknown OID"
        msg["meta"]["mib_resolution"] = mib
        msg["meta"]["investigation"] = f"SNMP MIB: {mib}"
        
    if source == "OSC" or "osc_address" in msg["meta"]:
        osc_addr = msg["meta"].get("osc_address", 
                                   "/" + topic.replace("OPEN-AIR/", ""))
        msg["meta"]["investigation"] = f"OSC Map: {osc_addr}"

    if source == "MIDI" or "midi_raw" in msg["meta"]:
        raw = msg["meta"].get("midi_raw", "Unknown Msg")
        port = msg["meta"].get("midi_port", "Remote")
        m_type = msg["meta"].get("midi_type", "msg")
        
        if "clock" in raw.lower():
            msg["meta"]["investigation"] = f"🎹 MIDI [CLOCK] from {port}"
        else:
            msg["meta"]["investigation"] = f"🎹 MIDI [{m_type.upper()}] " \
                                            f"from {port}"

    if "YAK" in topic.upper():
        if any(k in topic.upper() for k in ["SET", "NAB", "LEVEL", "FREQ"]):
            msg["meta"]["mutation"] = True
            msg["meta"]["investigation"] = "🚨 YAK Hardware Mutation"

    if msg["meta"].get("splink_active"):
        s_id = msg["meta"].get("splink_id", "Link")
        s_dest = msg["meta"].get("splink_dest", "Destination")
        msg["meta"]["investigation"] = f"🔗 Splink Sync [{s_id}] ➜ {s_dest}"

    val_str = str(msg["val"])
    if len(val_str) > 1000:
        msg["meta"]["blob"] = True
        msg["meta"]["investigation"] = f"📦 Large Configuration Blob " \
                                        f"({len(val_str)} bytes)"
