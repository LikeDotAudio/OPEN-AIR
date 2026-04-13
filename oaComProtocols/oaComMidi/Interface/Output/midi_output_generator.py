# oaComProtocols.oaComMidi/Interface/Output/midi_output_generator.py
#
# MIDI Output Generator GUI.
#
# Author: Anthony Peter Kuzub
# Version: 20260412.0015.1

import tkinter as tk
from tkinter import ttk
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log
from ..Input.midi_keyboard import MidiKeyboard, get_midi_color

class MidiOutputGenerator(tk.Frame):
    """
    MIDI Output Generator with interactive keyboard and channel selection.
    """
    def __init__(self, parent, midi_manager=None, **kwargs):
        self.config_data = kwargs.pop("config", {})
        self.midi_manager = midi_manager
        super().__init__(parent, **kwargs)
        
        if not self.midi_manager:
            self.midi_manager = self._find_midi_manager(parent)
        
        self.selected_channels = [tk.BooleanVar(value=False) for _ in range(16)]
        self.selected_channels[0].set(True) # Default Ch 1
        self.all_channels_var = tk.BooleanVar(value=False)
        self.send_enabled_var = tk.BooleanVar(value=True)
        self.selected_output_port = tk.StringVar()
        
        self._setup_ui()
        self._refresh_ports()

    def _find_midi_manager(self, widget):
        curr = widget
        while curr:
            if hasattr(curr, 'midi_manager'):
                m = getattr(curr, 'midi_manager', None)
                if m: return m
            app = getattr(curr, 'app_instance', None)
            if app and hasattr(app, 'midi_manager'):
                m = getattr(app, 'midi_manager', None)
                if m: return m
            try:
                if curr == curr.master: break
                curr = curr.master
            except: break
        return None

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")
        
        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="🎹 MIDI OUTPUT GENERATOR", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        tk.Checkbutton(header, text="ENABLE MIDI OUT", variable=self.send_enabled_var, 
                       bg="#2b2b2b", fg="#00ff00", selectcolor="#000000", font=("Helvetica", 10, "bold")).pack(side=tk.RIGHT, padx=20)

        main_pane = tk.Frame(self, bg="#2b2b2b")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Interactive Keyboard ---
        kb_frame = tk.LabelFrame(main_pane, text="Interactive Keyboard (Touch to Play)", bg="#2b2b2b", fg="#888888")
        kb_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.keyboard = MidiKeyboard(kb_frame, height=300, 
                                     on_note_on=self._generate_note_on, 
                                     on_note_off=self._generate_note_off)
        self.keyboard.pack(fill=tk.X, expand=True, padx=10, pady=10)

        # --- MIDDLE: Output Selection ---
        out_frame = tk.LabelFrame(main_pane, text="Output Hardware Selector", bg="#2b2b2b", fg="#888888")
        out_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.port_combo = ttk.Combobox(out_frame, textvariable=self.selected_output_port, state="readonly")
        self.port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        ttk.Button(out_frame, text="Refresh", command=self._refresh_ports).pack(side=tk.RIGHT, padx=10)

        # --- BOTTOM: Channel Selector ---
        ch_frame = tk.LabelFrame(main_pane, text="MIDI Channel Selector", bg="#2b2b2b", fg="#888888")
        ch_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        grid_frame = tk.Frame(ch_frame, bg="#2b2b2b")
        grid_frame.pack(padx=10, pady=10)
        
        for i in range(16):
            cb = tk.Checkbutton(grid_frame, text=f"Ch {i+1}", variable=self.selected_channels[i],
                                bg="#2b2b2b", fg=get_midi_color(i), selectcolor="#000000",
                                activebackground="#333333", activeforeground=get_midi_color(i))
            cb.grid(row=i//8, column=i%8, padx=5, pady=2, sticky="w")
            
        tk.Checkbutton(ch_frame, text="SELECT ALL CHANNELS", variable=self.all_channels_var, command=self._on_all_channels_toggle,
                       bg="#2b2b2b", fg="#ffffff", selectcolor="#000000").pack(pady=(0,10))

    def _refresh_ports(self):
        if not self.midi_manager: return
        info = self.midi_manager.get_port_info()
        outputs = info.get("outputs", [])
        self.port_combo['values'] = outputs
        if outputs and not self.selected_output_port.get():
            self.selected_output_port.set(outputs[0])

    def _on_all_channels_toggle(self):
        value = self.all_channels_var.get()
        for var in self.selected_channels:
            var.set(value)

    def _generate_note_on(self, note):
        if not self.send_enabled_var.get(): return
        self._send_midi("note_on", note, 100)

    def _generate_note_off(self, note):
        if not self.send_enabled_var.get(): return
        self._send_midi("note_off", note, 0)

    def _send_midi(self, m_type, note, velocity):
        if not self.midi_manager: return
        
        channels = [i for i, v in enumerate(self.selected_channels) if v.get()]
        if not channels: return
        
        color = get_midi_color(channels[0])
        if m_type == "note_on": self.keyboard.note_on(note, color)
        else: self.keyboard.note_off(note)

        port = self.selected_output_port.get()
        for ch in channels:
            topic = f"OPEN-AIR/MIDI/gui_out/ch{ch+1}/note{note}"
            pld = {
                "value": velocity, "channel": ch, "note": note, "velocity": velocity,
                "type": m_type, "raw": f"{m_type} channel={ch} note={note} velocity={velocity}"
            }
            meta = {
                "origin_source": "MIDI-TX", "target_port": port, "midi_type": m_type
            }
            import mido
            midi_message = mido.Message(m_type, channel=ch, note=note, velocity=velocity)
            try:
                # ⚡ REFACTORED: MidiManager.publish expects (port_name, mido_message)
                self.midi_manager.publish(port, midi_message)
            except Exception as e:
                logger.error(f"Failed to publish MIDI message: {e}")

def get_gui_class():
    return MidiOutputGenerator
