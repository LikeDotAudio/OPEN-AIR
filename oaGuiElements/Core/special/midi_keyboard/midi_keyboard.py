# midi_keyboard/midi_keyboard.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from loguru import logger

# Resistor Color Code Mapping & MIDI Channel Logic
# 1: Brown, 2: Red, 3: Orange, 4: Yellow, 5: Green, 6: Blue, 7: Violet, 8: Gray, 9: White
# Channels 10-16: ROYGBIVW (Red, Orange, Yellow, Green, Blue, Indigo, Violet, White)
RESISTOR_COLORS = {
    0: "#000000", # Black (used for off/bg)
    1: "#8B4513", # Brown
    2: "#FF0000", # Red
    3: "#FF8C00", # Orange
    4: "#FFFF00", # Yellow
    5: "#00FF00", # Green
    6: "#0000FF", # Blue
    7: "#EE82EE", # Violet
    8: "#808080", # Gray
    9: "#FFFFFF"  # White
}

# ROYGBIVW sequence for wrapping
WRAP_COLORS = [
    "#FF0000", # Red
    "#FF8C00", # Orange
    "#FFFF00", # Yellow
    "#00FF00", # Green
    "#0000FF", # Blue
    "#4B0082", # Indigo
    "#EE82EE", # Violet
    "#FFFFFF"  # White
]

def get_midi_color(channel):
    """Returns the color based on MIDI channel (1-16 typically)."""
    # Channel is usually 0-15 in mido, but 1-16 in user terms.
    # We'll treat the input as 0-indexed if it's from msg.channel
    ch = channel + 1 # Convert to 1-indexed for logic
    
    if 1 <= ch <= 9:
        return RESISTOR_COLORS.get(ch, "#FFFFFF")
    else:
        # Wrap around starting from Red
        idx = (ch - 10) % len(WRAP_COLORS)
        return WRAP_COLORS[idx]

class MidiKeyboard(tk.Canvas):
    """
    A 6-octave MIDI Keyboard Visualizer.
    Octaves: C1 to C7 (73 keys total for 6 full octaves + high C).
    Highlights keys using resistor color codes based on MIDI channel.
    """
    def __init__(self, parent, **kwargs):
        self.width = kwargs.get("width", 800)
        self.height = kwargs.get("height", 100)
        super().__init__(parent, width=self.width, height=self.height, bg="#1a1a1a", highlightthickness=0, bd=0)
        
        self.num_octaves = 6
        self.start_note = 36 # C1
        self.num_keys = (self.num_octaves * 12) + 1 # 73 keys
        
        self.white_keys = []
        self.black_keys = []
        self.key_map = {} # MIDI Note -> Canvas ID
        
        self._setup_keys()
        self.bind("<Configure>", self._on_resize)

    def _setup_keys(self):
        self.delete("all")
        self.key_map.clear()
        
        # Determine dimensions
        # Total white keys in 6 octaves + 1 high C
        num_white_keys = (self.num_octaves * 7) + 1
        kw = self.width / num_white_keys
        kh = self.height
        
        # 1. Draw White Keys first (Bottom Layer)
        current_x = 0
        for i in range(self.num_keys):
            note = self.start_note + i
            note_in_octave = note % 12
            is_black = note_in_octave in [1, 3, 6, 8, 10]
            
            if not is_black:
                rect = self.create_rectangle(
                    current_x, 0, current_x + kw, kh, 
                    fill="#ffffff", outline="#333333", tags=("white", f"note_{note}")
                )
                self.key_map[note] = rect
                current_x += kw

        # 2. Draw Black Keys (Top Layer)
        current_x = 0
        white_key_index = 0
        for i in range(self.num_keys):
            note = self.start_note + i
            note_in_octave = note % 12
            is_black = note_in_octave in [1, 3, 6, 8, 10]
            
            if is_black:
                # Black keys are positioned between white keys
                # Shift slightly back to center over the gap
                bx = current_x - (kw * 0.3)
                rect = self.create_rectangle(
                    bx, 0, bx + (kw * 0.6), kh * 0.6,
                    fill="#000000", outline="#333333", tags=("black", f"note_{note}")
                )
                self.key_map[note] = rect
            else:
                current_x += kw
                white_key_index += 1

    def _on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self._setup_keys()

    def handle_midi(self, msg):
        """Processes a mido message or a dict mirror."""
        try:
            m_type = ""
            channel = 0
            note = 0
            velocity = 0
            
            if isinstance(msg, dict):
                # It's a mirror from Core
                raw = msg.get("raw", "")
                # Poor man's parse if object not available, 
                # but we should have channel/note in internal mapping if we updated midi_manager.
                # Let's assume we might need to parse the raw string or use the dict fields.
                # If we updated midi_manager correctly, we can pass better info.
                
                # Check if we have pre-parsed fields (if I add them to midi_manager)
                channel = msg.get("channel", 0)
                note = msg.get("note", 0)
                velocity = msg.get("velocity", 0)
                m_type = msg.get("type", "note_on" if "note_on" in raw else "note_off")
                
                # Fallback parse raw string if needed
                if note == 0 and "note=" in raw:
                    parts = raw.split()
                    for p in parts:
                        if p.startswith("channel="): channel = int(p.split("=")[1])
                        if p.startswith("note="): note = int(p.split("=")[1])
                        if p.startswith("velocity="): velocity = int(p.split("=")[1])
            else:
                # It's a real mido message
                m_type = msg.type
                channel = msg.channel if hasattr(msg, "channel") else 0
                note = msg.note if hasattr(msg, "note") else 0
                velocity = msg.velocity if hasattr(msg, "velocity") else 0

            if m_type in ["note_on", "note_off"]:
                color = get_midi_color(channel)
                
                if m_type == "note_on" and velocity > 0:
                    self.note_on(note, color)
                else:
                    self.note_off(note)
        except Exception as e:
            logger.error(f"🎹 Keyboard Visualizer Error: {e}")

    def note_on(self, note, color):
        if note in self.key_map:
            self.itemconfig(self.key_map[note], fill=color)

    def note_off(self, note):
        if note in self.key_map:
            # Revert to original
            note_in_octave = note % 12
            is_black = note_in_octave in [1, 3, 6, 8, 10]
            orig_fill = "#000000" if is_black else "#ffffff"
            self.itemconfig(self.key_map[note], fill=orig_fill)
