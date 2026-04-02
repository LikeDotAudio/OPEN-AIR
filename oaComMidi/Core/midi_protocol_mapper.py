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
                # Try to extract the name before the colon (ALSA style)
                # E.g., 'Arturia MicroLab:Arturia MicroLab  32:0' -> 'Arturia MicroLab'
                name_part = port_name.split(':')[0]
                # Sanitize: lowercase and replace non-alphanumeric with underscore
                dev_id = re.sub(r'[^a-zA-Z0-9]', '_', name_part).lower().strip('_')
                # Collapse multiple underscores
                dev_id = re.sub(r'_{2,}', '_', dev_id)
                
            self._dev_id_cache[port_name] = dev_id
        
        ch = msg.channel if hasattr(msg, 'channel') else 0
        base = f"OPEN-AIR/MIDI/{dev_id}/ch{ch}"
        
        if msg.type == 'control_change': return f"{base}/cc{msg.control}", msg.value
        if msg.type in ['note_on', 'note_off']: return f"{base}/note{msg.note}", (msg.velocity if msg.type == 'note_on' else 0)
        return f"{base}/{msg.type}", 0

    def topic_to_midi(self, topic, val):
        """Logic for reverse mapping Internal -> MIDI."""
        if "/MIDI/" not in topic: return None
        
        try:
            parts = topic.split('/')
            # OPEN-AIR / MIDI / dev_id / chX / type
            if len(parts) < 5: return None
            
            ch_str = parts[3] # e.g. "ch0"
            type_str = parts[4] # e.g. "cc7" or "note60"
            
            channel = int(re.search(r"\d+", ch_str).group(0))
            
            import mido
            if "cc" in type_str:
                control = int(re.search(r"\d+", type_str).group(0))
                return mido.Message('control_change', channel=channel, control=control, value=int(val))
            
            if "note" in type_str:
                note = int(re.search(r"\d+", type_str).group(0))
                velocity = int(val)
                m_type = 'note_on' if velocity > 0 else 'note_off'
                return mido.Message(m_type, channel=channel, note=note, velocity=velocity)
                
            return None
        except Exception:
            return None
