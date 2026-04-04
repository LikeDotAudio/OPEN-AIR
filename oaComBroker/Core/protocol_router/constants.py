# Core/protocol_router/constants.py
#
# Shared constants and emoji-based routing definitions for the Protocol Router.
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
# Version 20260328.1435.1
#
# Description:
# This module defines the static configuration and routing maps used by the
# ProtocolRouter. It employs a unique emoji-based strategy system to visually
# represent the lifecycle and destination of messages as they traverse the
# partitioned architecture.
#
# Architectural Role:
# - Provides a central source of truth for protocol-to-emoji mapping.
# - Defines human-readable descriptions for forensic telemetry.
# - Houses global debug gates and application constant proxies.

from oaConfiguration.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import is_debug_allowed

# Proxy for globally loaded application settings (GUIDs, Base Topics, etc.)
app_constants = Config.get_instance()

# --- Standard Debug Logging Setup ---
# The router respects the hierarchical debug matrix. 
# It is classified under the 'ROUTER' element within the 'router' system.
def GET_LOCAL_DEBUG(func_name=None):
    return is_debug_allowed(system="comms", element="broker", func_name=func_name)

# Legacy compatibility (defaults to checking the system/element level)
LOCAL_DEBUG = GET_LOCAL_DEBUG()

# --- Default Routing Strategy Map ---
# Each protocol is assigned a set of emoji tokens that dictate where a message 
# from that source should be routed.
#
# Tokens:
# 🚀 [PUSH]   - Broadcast to external network (MQTT).
# 💾 [CACHE]  - Persist to local state registry.
# Ⓖ [GUI]    - Dispatch to local UI observers.
# 🅾️ [OSC]    - Dispatch to remote OSC managers.
# 🎹 [MIDI]   - Dispatch to physical MIDI hardware.
# Ⓜ️ [MQTT]   - Explicit MQTT reflection.
# Ⓢ [SNMP]   - Dispatch to network infrastructure.
SINK_STRATEGIES = {
    "OSC": "🅾️ 🚀 💾 Ⓖ",
    "MIDI": "🎹 🚀 💾 Ⓖ",
    "SNMP": "Ⓢ 🚀 💾 Ⓖ",
    "MQTT": "Ⓜ️ 🚀 💾 Ⓖ 🎹",
    "REST": "Ⓜ️ 🚀 💾 Ⓖ",
    "DISK": "💾 🚀 Ⓖ",
    "OSC-TX": "💾 Ⓖ",
    "SPLINKER": "🔗 🚀 💾 Ⓖ"
}

# --- Emoji to Word Mapping for DPI Reports ---
# Used by the Monitor to translate cryptic strategy strings into 
# human-readable forensic reports.
EMOJI_TO_WORD = {
    "Ⓖ": "GUI", 
    "Ⓜ️": "MQTT", 
    "🅾️": "OSC", 
    "Ⓢ": "SNMP", 
    "🎹": "MIDI",
    "💾": "CACHE", 
    "🚀": "PUSH", 
    "⚙️": "SYSTEM", 
    "🔗": "LINK"
}

# --- Transport Source Descriptions ---
# Detailed forensic descriptions used in Packet Investigation Reports.
SOURCE_DESCRIPTIONS = {
    "GUI": "Ⓖ [Local User Interface] - Direct user interaction.",
    "MQTT": "Ⓜ️ [MQTT Broker] - External asynchronous network data.",
    "REST": "🌐 [REST API] - Stateless web command or integration.",
    "OSC": "🅾️ [OSC Device] - Remote control surface command.",
    "MIDI": "🎹 [MIDI Device] - Physical note or CC received.",
    "MIDI-TX": "🎹 [MIDI Output] - Hardware command acknowledgement.",
    "SNMP": "Ⓢ [SNMP Manager] - Network management request.",
    "DISK": "💾 [Local Storage] - Cold-boot state restoration.",
    "SPLINKER": "🔗 [Splinker Hub] - Inter-module brokered command link.",
    "GUI-INIT": "⚙️ [Discovery] - Automated topic namespace scan.",
    "GUI-LOAD": "⚙️ [Initialization] - Synchronous boot sequence."
}
