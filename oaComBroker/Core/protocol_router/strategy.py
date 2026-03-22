# protocol_router/strategy.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic for calculating routing strategies and UI tags.

from .constants import SINK_STRATEGIES, app_constants

def calculate_strategy(msg):
    """
    Determines the routing strategy for a message using emoji tokens.
    """
    topic = msg.get("topic")
    source = msg["source"]
    logical_source = msg.get("logical_source", source)
    full_id = msg.get("full_id")
    
    # Loop prevention: Reject messages from our own identity on the network.
    if source == "MQTT" and full_id == app_constants.FULL_INSTANCE_ID:
        return "IGNORE (REFLECT)"
        
    # Local GUI actions are broadcast to all available transport layers.
    if logical_source == "GUI":
        return "Ⓖ 🚀 💾 Ⓜ️ 🅾️ Ⓢ 🎹" 
        
    return SINK_STRATEGIES.get(logical_source, f"{logical_source} 🚀 💾 Ⓖ")

def calculate_ui_tags(msg, local_guid):
    """Pre-calculates metadata tags for UI treeview categorization."""
    logical_source = msg.get("logical_source", msg["source"])
    is_local = (msg["guid"] == local_guid)
    is_mutation = msg["meta"].get("mutation", False)
    
    tags = []
    if "-" in logical_source: 
        tags.append("SYSTEM")
    elif "MIDI" in logical_source:
        tags.append("MIDI")
    elif "OSC" in logical_source:
        tags.append("OSC")
    else:
        tags.append("HERE" if is_local else "REMOTE")
        
    if is_mutation:
        tags.append("MUTATION")
    if msg["meta"].get("splink_active") or msg["meta"].get("splinker_source"): 
        tags.append("SPLINK")
    return tags
