# workers/Command_Router/protocol_router/constants.py
#
# Shared constants and emoji-based routing definitions for the Protocol Router.

from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True

# --- Default Routing Strategy Map ---
SINK_STRATEGIES = {
    "OSC": "🅾️ 🚀 💾 Ⓖ",
    "MIDI": "🎹 🚀 💾 Ⓖ",
    "SNMP": "Ⓢ 🚀 💾 Ⓖ",
    "MQTT": "Ⓜ️ 🚀 💾 Ⓖ",
    "DISK": "💾 🚀 Ⓖ",
    "OSC-TX": "💾 Ⓖ",
    "SPLINKER": "🔗 🚀 💾 Ⓖ"
}

# --- Emoji to Word Mapping for DPI Reports ---
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
SOURCE_DESCRIPTIONS = {
    "GUI": "Ⓖ [Local User Interface] - User action.",
    "MQTT": "Ⓜ️ [MQTT Broker] - External network data.",
    "OSC": "🅾️ [OSC Device] - Remote control command.",
    "MIDI": "🎹 [MIDI Device] - Note or CC received.",
    "MIDI-TX": "🎹 [MIDI Output] - Hardware command sent.",
    "SNMP": "Ⓢ [SNMP Manager] - Network request.",
    "DISK": "💾 [Local Storage] - State restoration.",
    "SPLINKER": "🔗 [Splinker Hub] - Brokered command link.",
    "GUI-INIT": "⚙️ [Discovery] - Topic scan.",
    "GUI-LOAD": "⚙️ [Initialization] - Boot sync."
}
