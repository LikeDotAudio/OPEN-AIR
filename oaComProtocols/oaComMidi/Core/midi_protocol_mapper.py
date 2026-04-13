# oaComProtocols.oaComMidi/Core/midi_protocol_mapper.py
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
import sys
from pathlib import Path

# --- Iron Oxide Distributed Binary Standard ---
try:
    from oaRustCore import oa_midi_mapper_rs as oamidimapper_rs
    HAS_RUST_MIDI = True
except ImportError:
    import logging
    logging.warning("🚀⚠️ [MIDI] oaMidiMapper-rs missing. MIDI mapping will be non-functional.")
    HAS_RUST_MIDI = False

class MIDIProtocolMapper:
    """Handles bidirectional mapping between MIDI messages and system topics (RUST ACCELERATED)."""

    def __init__(self):
        self._dev_id_cache = {}

    def midi_to_topic(self, message, port_name):
        if not message: return "OPEN-AIR/MIDI/unknown/error", 0
        
        # 1. Device ID Sanitization (Rust)
        if port_name in self._dev_id_cache: 
            dev_id = self._dev_id_cache[port_name]
        else:
            dev_id = oamidimapper_rs.sanitize_id(port_name)
            self._dev_id_cache[port_name] = dev_id
        
        # 2. Topic Mapping (Rust)
        ch = message.channel if hasattr(message, 'channel') else 0
        note_or_cc = 0
        if hasattr(message, 'note'): note_or_cc = message.note
        elif hasattr(message, 'control'): note_or_cc = message.control
        
        value = 0
        if hasattr(message, 'velocity'): value = message.velocity
        elif hasattr(message, 'value'): value = message.value
        
        return oamidimapper_rs.midi_to_topic(dev_id, message.type, ch, note_or_cc, value)

    def topic_to_midi(self, topic, value):
        """Logic for reverse mapping Internal -> MIDI (Mixed Mode)."""
        if "/MIDI/" not in topic: return None
        
        try:
            # ⚡ Support for JSON dictionary payloads
            if isinstance(value, dict):
                real_val = int(value.get('value', value.get('velocity', value.get('value', 0))))
            else:
                real_val = int(value)

            # ⚡ V3.2.5 GUI_OUT ALIGNMENT:
            # Handle topics from the Output Generator: OPEN-AIR/MIDI/gui_out/chX/noteY
            if "/gui_out/" in topic:
                # Use regex to find the relevant parts regardless of exact indices
                ch_match = re.search(r'/ch(\d+)', topic)
                note_match = re.search(r'/note(\d+)', topic)
                cc_match = re.search(r'/cc(\d+)', topic)
                
                if not ch_match: return None
                channel = int(ch_match.group(1)) - 1
                
                import mido
                if note_match:
                    note = int(note_match.group(1))
                    velocity = real_val
                    m_type = 'note_on' if velocity > 0 else 'note_off'
                    return mido.Message(m_type, channel=channel, note=note, velocity=velocity)
                elif cc_match:
                    control = int(cc_match.group(1))
                    return mido.Message('control_change', channel=channel, control=control, value=real_val)
                
                return None

            parts = topic.split('/')
            if len(parts) < 5: return None
            
            # Use Rust for digit extraction (Speed + Safety)
            channel = oamidimapper_rs.parse_channel_and_val(parts[3])
            type_str = parts[4]
            
            import mido
            if "cc" in type_str:
                control = oamidimapper_rs.parse_channel_and_val(type_str)
                return mido.Message('control_change', channel=channel, control=control, value=real_val)
            
            if "note" in type_str:
                note = oamidimapper_rs.parse_channel_and_val(type_str)
                velocity = real_val
                m_type = 'note_on' if velocity > 0 else 'note_off'
                return mido.Message(m_type, channel=channel, note=note, velocity=velocity)
                
            return None
        except Exception:
            return None
