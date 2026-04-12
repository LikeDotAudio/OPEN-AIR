# midi_keyboard/midi_keyboard.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Interactive MIDI Keyboard Visualizer & Input Component.

import tkinter as tk
from loguru import logger
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from oaLogging.Methods.matrix_gate import matrix_log

# Resistor Color Code Mapping & MIDI Channel Logic
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
    """Returns the color based on MIDI channel (0-15 typical in mido)."""
    # Map to 1-indexed for the resistor color logic
    ch = channel + 1
    
    if 1 <= ch <= 9:
        return RESISTOR_COLORS.get(ch, "#FFFFFF")
    else:
        # Wrap around starting from Red
        idx = (ch - 10) % len(WRAP_COLORS)
        return WRAP_COLORS[idx]

@WidgetRegistry.register("MidiKeyboard", "MIDI_KEYBOARD")
class MidiKeyboard(tk.Canvas):
    """
    A 6-octave MIDI Keyboard Visualizer & Input Component.
    Octaves: C1 to C7 (73 keys total for 6 full octaves + high C).
    Highlights keys using resistor color codes based on MIDI channel.
    Supports mouse interaction for generating MIDI-like events.
    """
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        self.width = kwargs.get("width", 800)
        self.height = kwargs.get("height", 100)
        
        # Callbacks for interactivity (passed via config or kwargs)
        self.on_note_on = self.config_data.get("on_note_on") or kwargs.get("on_note_on")
        self.on_note_off = self.config_data.get("on_note_off") or kwargs.get("on_note_off")

        super().__init__(parent, width=self.width, height=self.height, bg="#1a1a1a", highlightthickness=0, bd=0)
        
        self.num_octaves = 6
        self.start_note = 36 # C1
        self.num_keys = (self.num_octaves * 12) + 1 # 73 keys
        
        self.key_map = {} # MIDI Note -> Canvas ID
        self.id_to_note = {} # Canvas ID -> MIDI Note
        self.active_mouse_notes = set() # Currently pressed notes via mouse
        
        self._setup_keys()
        self.bind("<Configure>", self._on_resize)
        
        # Interactivity Bindings
        self.bind("<Button-1>", self._on_mouse_press)
        self.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.bind("<B1-Motion>", self._on_mouse_motion)

    def _setup_keys(self):
        self.delete("all")
        self.key_map.clear()
        self.id_to_note.clear()
        
        # Determine dimensions
        num_white_keys = (self.num_octaves * 7) + 1
        kw = self.width / num_white_keys if num_white_keys > 0 else 10
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
                self.id_to_note[rect] = note
                current_x += kw

        # 2. Draw Black Keys (Top Layer)
        current_x = 0
        for i in range(self.num_keys):
            note = self.start_note + i
            note_in_octave = note % 12
            is_black = note_in_octave in [1, 3, 6, 8, 10]
            
            if is_black:
                # Black keys are positioned between white keys
                bx = current_x - (kw * 0.3)
                rect = self.create_rectangle(
                    bx, 0, bx + (kw * 0.6), kh * 0.6,
                    fill="#000000", outline="#333333", tags=("black", f"note_{note}")
                )
                self.key_map[note] = rect
                self.id_to_note[rect] = note
            else:
                current_x += kw

    def _on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self._setup_keys()

    # --- Mouse Interaction ---

    def _on_mouse_press(self, event):
        items = self.find_closest(event.x, event.y)
        if not items: return
        item = items[0]
        note = self.id_to_note.get(item)
        if note and note not in self.active_mouse_notes:
            self.active_mouse_notes.add(note)
            if self.on_note_on:
                self.on_note_on(note)
            # Visual feedback is handled via handle_midi if looped back, 
            # or we can force it here for immediate response.
            self.note_on(note, "#00ffff") # Cyan for mouse-over/press

    def _on_mouse_release(self, event):
        for note in list(self.active_mouse_notes):
            if self.on_note_off:
                self.on_note_off(note)
            self.note_off(note)
        self.active_mouse_notes.clear()

    def _on_mouse_motion(self, event):
        items = self.find_closest(event.x, event.y)
        if not items: return
        item = items[0]
        note = self.id_to_note.get(item)
        
        if note and note not in self.active_mouse_notes:
            # Release old notes
            for old_note in list(self.active_mouse_notes):
                if self.on_note_off:
                    self.on_note_off(old_note)
                self.note_off(old_note)
            self.active_mouse_notes.clear()
            
            # Press new note
            self.active_mouse_notes.add(note)
            if self.on_note_on:
                self.on_note_on(note)
            self.note_on(note, "#00ffff")

    # --- MIDI Handling ---

    def handle_midi(self, msg):
        """Processes a mido message or a dict mirror."""
        try:
            m_type = ""
            channel = 0
            note = 0
            velocity = 0
            
            matrix_log("comms", "midi", "handle_midi", f"🎹 [KEYBOARD] Incoming MIDI: {msg}", "DEBUG")

            if isinstance(msg, dict):
                channel = msg.get("channel", 0)
                note = msg.get("note", 0)
                velocity = msg.get("velocity", msg.get("val", 0))
                # Fallback to parsing 'raw' if fields are missing
                if note == 0 and "raw" in msg:
                    raw = msg["raw"]
                    m_type = "note_on" if "note_on" in raw else "note_off"
                    # Simple regex-like extraction
                    import re
                    n_match = re.search(r"note=(\d+)", raw)
                    if n_match: note = int(n_match.group(1))
                    c_match = re.search(r"channel=(\d+)", raw)
                    if c_match: channel = int(c_match.group(1))
                    v_match = re.search(r"velocity=(\d+)", raw)
                    if v_match: velocity = int(v_match.group(1))
                else:
                    m_type = msg.get("type", "note_on" if velocity > 0 else "note_off")
            else:
                m_type = msg.type
                channel = msg.channel if hasattr(msg, "channel") else 0
                note = msg.note if hasattr(msg, "note") else 0
                velocity = msg.velocity if hasattr(msg, "velocity") else 0

            if m_type in ["note_on", "note_off"]:
                color = get_midi_color(channel)
                matrix_log("comms", "midi", "handle_midi", f"🎹 [KEYBOARD] Dispatching: type={m_type}, note={note}, channel={channel}, color={color}", "DEBUG")
                if m_type == "note_on" and velocity > 0:
                    self.note_on(note, color)
                else:
                    self.note_off(note)
        except Exception as e:
            matrix_log("comms", "midi", "handle_midi", f"🎹 ❌ Keyboard Visualizer Error: {e}", "ERROR")
            logger.error(f"🎹 Keyboard Visualizer Error: {e}")

    def note_on(self, note, color):
        if note in self.key_map:
            self.itemconfig(self.key_map[note], fill=color)

    def note_off(self, note):
        if note in self.key_map:
            # Revert to original color (black or white)
            note_in_octave = note % 12
            is_black = note_in_octave in [1, 3, 6, 8, 10]
            orig_fill = "#000000" if is_black else "#ffffff"
            self.itemconfig(self.key_map[note], fill=orig_fill)

def get_gui_class():
    return MidiKeyboard
