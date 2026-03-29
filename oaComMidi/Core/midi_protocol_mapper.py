# oaComMidi/Core/midi_protocol_mapper.py
#
# Bidirectional mapping between MIDI messages and system topics.
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
# Version 20260328.1425.1

import re

class MIDIProtocolMapper:
    """Handles bidirectional mapping between MIDI messages and system topics."""

    def __init__(self):
        self._dev_id_cache = {}

    def midi_to_topic(self, msg, port_name):
        if port_name in self._dev_id_cache: dev_id = self._dev_id_cache[port_name]
        else:
            dev_id = "unknown"
            if port_name:
                m = re.search(r"(\d+:\d+)", port_name)
                dev_id = m.group(1).replace(":", "_") if m else re.sub(r'[^a-zA-Z0-9]', '_', port_name).lower().strip('_')
            self._dev_id_cache[port_name] = dev_id
        
        ch = msg.channel if hasattr(msg, 'channel') else 0
        base = f"OPEN-AIR/MIDI/{dev_id}/ch{ch}"
        
        if msg.type == 'control_change': return f"{base}/cc{msg.control}", msg.value
        if msg.type in ['note_on', 'note_off']: return f"{base}/note{msg.note}", (msg.velocity if msg.type == 'note_on' else 0)
        return f"{base}/{msg.type}", 0

    def topic_to_midi(self, topic, val):
        """Logic for reverse mapping Internal -> MIDI (To be implemented)."""
        return None
