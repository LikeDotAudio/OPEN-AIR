# Core/protocol_router/strategy.py
#
# Logic for calculating routing strategies and UI tags for message prioritization.
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
# Version 20260328.1445.1
#
# Description:
# This module implements the "Traffic Control" phase of the ProtocolRouter.
# It calculates the emoji-based strategy string that dictates how a packet
# should be dispatched. It also pre-calculates UI-friendly tags for efficient
# filtering in the frontend treeviews.
#
# Architectural Role:
# - Serves as the primary routing engine for the partitioned architecture.
# - Implements network-level loop prevention (Reflection rejection).
# - Decouples high-level routing policy from low-level transport management.

from .constants import SINK_STRATEGIES, app_constants

def calculate_strategy(msg):
    """
    Determines the routing strategy for a message using emoji tokens.
    
    This function analyzes the message origin and logical source to assign 
    a destination strategy based on the dynamic N x N routing matrix.
    """
    topic = msg.get("topic")
    source = msg["source"]
    logical_source = msg.get("logical_source", source)
    full_id = msg.get("full_id")
    
    # --- Loop Prevention: Network Reflection Rejection ---
    # ⚡ V3.1.21 REFLECTION PURGE:
    # All messages arriving from MQTT that were authored by this instance 
    # must be tagged for IGNORE. They still reach the local Monitor/Firehose 
    # via the ingest pipeline but are blocked from re-dispatch.
    if source == "MQTT" and full_id == app_constants.FULL_INSTANCE_ID:
        return "IGNORE (REFLECT)"
        
    # --- Dynamic Matrix Routing ---
    from .manager import ProtocolRouter
    router = ProtocolRouter.get_instance()
    
    strategy = router.calculate_strategy_for_msg(logical_source, topic)
    
    if not strategy:
        # Default fallback for untracked sources
        return "Ⓖ 🚀"
        
    return strategy

def calculate_ui_tags(msg, local_guid):
    """
    Pre-calculates metadata tags for UI treeview categorization.
    
    Tags allow the frontend to instantly filter messages by protocol, 
    origin, or functional type (e.g., MUTATION, SPLINK).
    
    Args:
        msg (dict): The normalized message packet.
        local_guid (str): The GUID of the local instance.
        
    Returns:
        list[str]: A list of uppercase tag tokens.
    """
    logical_source = msg.get("logical_source", msg["source"])
    is_local = (msg["guid"] == local_guid)
    is_mutation = msg["meta"].get("mutation", False)
    
    tags = []
    
    # --- Protocol-Level Tagging ---
    if "-" in logical_source: 
        tags.append("SYSTEM")
    elif "MIDI" in logical_source:
        tags.append("MIDI")
    elif "OSC" in logical_source:
        tags.append("OSC")
    else:
        # Geographic origin tagging.
        tags.append("HERE" if is_local else "REMOTE")
        
    # --- Functional Tagging ---
    if is_mutation:
        # Flag hardware control events (YAK).
        tags.append("MUTATION")
    if msg["meta"].get("splink_active") or msg["meta"].get("splinker_source"): 
        # Flag patched/linked parameters.
        tags.append("SPLINK")
        
    return tags
