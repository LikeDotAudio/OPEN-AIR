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
from .oaMidiMapper_rs.compiler_hook import ensure_compiled
ensure_compiled()
try:
    import oamidimapper_rs
except ImportError:
    # CRITICAL: Pure Rust mandate. Fallback prohibited.
    raise ImportError("🚀❌ [FATAL] oaMidiMapper-rs binary missing. Iron Oxide mode mandatory.")

class MIDIProtocolMapper:
    """Handles bidirectional mapping between MIDI messages and system topics (RUST ACCELERATED)."""

    def __init__(self):
        self._dev_id_cache = {}

    def midi_to_topic(self, msg, port_name):
        if not msg: return "OPEN-AIR/MIDI/unknown/error", 0
        
        # 1. Device ID Sanitization (Rust)
        if port_name in self._dev_id_cache: 
            dev_id = self._dev_id_cache[port_name]
        else:
            dev_id = oamidimapper_rs.sanitize_id(port_name)
            self._dev_id_cache[port_name] = dev_id
        
        # 2. Topic Mapping (Rust)
        ch = msg.channel if hasattr(msg, 'channel') else 0
        note_or_cc = 0
        if hasattr(msg, 'note'): note_or_cc = msg.note
        elif hasattr(msg, 'control'): note_or_cc = msg.control
        
        val = 0
        if hasattr(msg, 'velocity'): val = msg.velocity
        elif hasattr(msg, 'value'): val = msg.value
        
        return oamidimapper_rs.midi_to_topic(dev_id, msg.type, ch, note_or_cc, val)

    def topic_to_midi(self, topic, val):
        """Logic for reverse mapping Internal -> MIDI (Mixed Mode)."""
        if "/MIDI/" not in topic: return None
        
        try:
            parts = topic.split('/')
            if len(parts) < 5: return None
            
            # Use Rust for digit extraction (Speed + Safety)
            channel = oamidimapper_rs.parse_channel_and_val(parts[3])
            type_str = parts[4]
            
            import mido
            if "cc" in type_str:
                control = oamidimapper_rs.parse_channel_and_val(type_str)
                return mido.Message('control_change', channel=channel, control=control, value=int(val))
            
            if "note" in type_str:
                note = oamidimapper_rs.parse_channel_and_val(type_str)
                velocity = int(val)
                m_type = 'note_on' if velocity > 0 else 'note_off'
                return mido.Message(m_type, channel=channel, note=note, velocity=velocity)
                
            return None
        except Exception:
            return None
