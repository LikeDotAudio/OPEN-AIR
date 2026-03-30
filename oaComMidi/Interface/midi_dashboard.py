# oaComMidi/Interface/midi_dashboard.py
#
# MIDI Port & Activity Dashboard Plugin for OPEN-AIR.
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
# Version 20260328.1430.1

import tkinter as tk
from tkinter import ttk
import datetime
from oaGuiElements.Core.utils.midi_keyboard.midi_keyboard import MidiKeyboard, get_midi_color

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger

class MidiDashboard(tk.Frame):
    """
    MIDI Port & Activity Dashboard.
    A 'Dumb Terminal' that reflects state from the MidiManager worker.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        self.midi_manager = self._find_midi_manager(parent)
        self._setup_ui()
        
        if self.midi_manager:
            if LOCAL_DEBUG: logger.debug("🎹 [MIDI-DASH] MidiManager found. Registering callback.")
            # Add a local callback for the dashboard monitor
            self.midi_manager.add_monitor_callback(self.on_midi_activity)
            self._refresh_ui()
        else:
            if LOCAL_DEBUG: logger.warning("🎹 [MIDI-DASH] MidiManager NOT found in widget tree.")

    def _find_midi_manager(self, widget):
        from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if hasattr(curr, 'midi_manager'):
                m = getattr(curr, 'midi_manager', None)
                if m: return m
            if isinstance(curr, DynamicGuiBuilder) and hasattr(curr, 'app_instance'):
                m = getattr(curr.app_instance, 'midi_manager', None)
                if m: return m
            try:
                curr = curr.master
            except Exception: break
        return None

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))
        tk.Label(header, text="🎹 MIDI CONTROLLER HUB", font=("Helvetica", 12, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        ttk.Button(header, text="Refresh Hardware List", command=self._refresh_ui).pack(side=tk.RIGHT, padx=20)

        # 2. Main Layout (Vertical Stack: Keyboard, Monitor then Ports)
        main_pane = tk.Frame(self, bg="#2b2b2b")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Keyboard Visualizer ---
        kb_frame = tk.LabelFrame(main_pane, text="Keyboard Visualizer (C1-C7)", bg="#2b2b2b", fg="#888888", font=("Helvetica", 9))
        kb_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.keyboard = MidiKeyboard(kb_frame, height=80)
        self.keyboard.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # --- MIDDLE: Live Monitor ---
        log_frame = tk.LabelFrame(main_pane, text="Live MIDI Feed (Monitor)", bg="#2b2b2b", fg="#888888", font=("Helvetica", 9))
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), height=14, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # --- BOTTOM: Ports List ---
        port_frame = tk.LabelFrame(main_pane, text="Detected Hardware Ports", bg="#2b2b2b", fg="#888888", font=("Helvetica", 9))
        port_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=5, pady=5)

        self.port_tree = ttk.Treeview(port_frame, columns=("Type", "Status"), show="tree headings", height=8)
        self.port_tree.heading("#0", text="Device Name")
        self.port_tree.heading("Type", text="Type")
        self.port_tree.heading("Status", text="Status")
        self.port_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _refresh_ui(self):
        """Pure UI refresh. Pulls all data from the Manager worker."""
        if not self.midi_manager: return
        
        # Clear existing
        for item in self.port_tree.get_children():
            self.port_tree.delete(item)
            
        # Get data from worker logic
        info = self.midi_manager.get_port_info()
        
        if info.get("error"):
            self.port_tree.insert("", "end", text="ERROR", values=("FAIL", info["error"]))
            return

        # Popoulate Inputs
        for name in info["inputs"]:
            status = "Active" if name in info["active_in"] else "Available"
            self.port_tree.insert("", "end", text=name, values=("INPUT", status), tags=("input",))
            
        # Populate Outputs
        for name in info["outputs"]:
            status = "Active" if name in info["active_out"] else "Available"
            self.port_tree.insert("", "end", text=name, values=("OUTPUT", status), tags=("output",))
            
        self.port_tree.tag_configure("input", foreground="#00aaff")
        self.port_tree.tag_configure("output", foreground="#ffaa00")

    def on_midi_activity(self, direction, msg):
        """Called by the manager when traffic occurs."""
        self.after(0, lambda: self._process_activity(direction, msg))

    def _process_activity(self, direction, msg):
        if LOCAL_DEBUG:
            logger.debug(f"🎹 [MIDI-DASH] Processing {direction} activity for UI update.")
        
        # 1. Update Keyboard
        self.keyboard.handle_midi(msg)
        
        # 2. Add to Log with channel-aware coloring
        channel = 0
        m_type = ""
        msg_str = ""
        
        if isinstance(msg, dict):
            # Enriched payload from CORE
            channel = msg.get("channel", 0)
            m_type = msg.get("type", "unknown")
            msg_str = msg.get("raw", str(msg))
        elif hasattr(msg, "channel"):
            channel = msg.channel
            m_type = msg.type
            msg_str = str(msg)
        else:
            msg_str = str(msg)
            
        self._add_log(direction, msg_str, channel)

    def _add_log(self, direction, msg_str, channel=0):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        color = get_midi_color(channel)
        
        # Create or reuse a tag for this specific color
        tag_name = f"ch_color_{color.replace('#', '')}"
        self.log_text.tag_configure(tag_name, foreground=color)
        
        formatted_line = f"[{ts}] {direction} >> {msg_str}\n"
        self.log_text.insert("1.0", formatted_line, tag_name)
        
        # Truncate
        if int(self.log_text.index('end-1c').split('.')[0]) > 200:
            self.log_text.delete('200.0', tk.END)

    def destroy(self):
        if self.midi_manager:
            try:
                self.midi_manager.remove_monitor_callback(self.on_midi_activity)
            except Exception as e:
                logger.trace(f"Failed to remove MIDI monitor callback: {e}")
        super().destroy()

def get_gui_class():
    return MidiDashboard
