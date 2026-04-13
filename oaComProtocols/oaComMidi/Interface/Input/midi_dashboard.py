# oaComProtocols.oaComMidi/Interface/Input/midi_dashboard.py
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1
#
# Description: MIDI Port & Activity Dashboard.
# A modular dashboard that handles hardware discovery, connections, 
# live monitoring, and keyboard visualization.

import tkinter as tk
from tkinter import ttk
import datetime
import inspect
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log
from .midi_keyboard import MidiKeyboard, get_midi_color

# --- Specialized Components ---

from .midi_feed import MidiFeed
from .midi_hardware import MidiHardware
from .midi_hardware_search import MidiHardwareSearch
from .midi_connection_manager import MidiConnectionManager

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False

class MidiDashboard(tk.Frame):
    """
    MIDI Port & Activity Dashboard.
    A modular dashboard that handles hardware discovery, connections, 
    live monitoring, and keyboard visualization.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        passed_manager = kwargs.pop("midi_manager", None)

        logger.info("🎹 [MIDI-DASH] __init__ called. Instantiating dashboard...")
        matrix_log("comms", "midi", "__init__", "🎹 [MIDI-DASH] Instantiating MidiDashboard...", "INFO")
        super().__init__(parent, **kwargs)
        self.midi_manager = passed_manager or self._find_midi_manager(parent)
        self._setup_ui()

        if self.midi_manager:
            logger.info(f"🎹 [MIDI-DASH] MidiManager found: {self.midi_manager}")
            matrix_log("comms", "midi", "__init__", f"🎹 [MIDI-DASH] MidiManager found ({'Bridge' if self.midi_manager.run_bridge else 'Observer'}). Registering callback.", "SUCCESS")
            # Add a local callback for the dashboard monitor
            self.midi_manager.add_monitor_callback(self.on_midi_activity)
            self._refresh_ui()
        else:
            logger.error("🎹 [MIDI-DASH] ❌ CRITICAL: MidiManager NOT found in widget tree.")
            matrix_log("comms", "midi", "__init__", "🎹 [MIDI-DASH] ❌ CRITICAL: MidiManager NOT found in widget tree. Fallback to ProtocolRouter.", "WARNING")
            
            # Fallback: Listen to the ProtocolRouter directly for MIDI traffic
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            ProtocolRouter.get_instance().register_cache_observer(self._on_protocol_event)

    def _find_midi_manager(self, widget):
        # 1. Check direct configuration first
        if self.config_data.get("midi_manager"):
            return self.config_data.get("midi_manager")
        
        # 2. Check app_instance from configuration
        app = self.config_data.get("app_instance")
        if app and hasattr(app, "midi_manager"):
            m = getattr(app, "midi_manager", None)
            if m: return m

        # 3. Traverse the widget tree upwards
        curr = widget
        while curr:
            # Check for direct attribute
            m = getattr(curr, 'midi_manager', None)
            if m: return m
            
            # Check for nested app_instance
            a = getattr(curr, 'app_instance', None)
            if a and hasattr(a, 'midi_manager'):
                m = getattr(a, 'midi_manager', None)
                if m: return m
                
            try:
                if curr == curr.master: break # Reached root
                curr = curr.master
            except Exception: break
            
        # 4. Global Lookup fallback (Last Resort)
        try:
            from oaComProtocols.oaComMidi.Entry import get_manager
            return get_manager()
        except: return None

    def _on_protocol_event(self, message):
        """Observer callback for ProtocolRouter traffic."""
        topic = str(message.get("topic", ""))
        is_midi_topic = "/MIDI/" in topic
        is_midi_source = message.get("logical_source") in ["MIDI", "MIDI-TX"]
        
        matrix_log("comms", "midi", "_on_protocol_event", f"🎹 [DASH] Protocol Event: topic={topic}, source={message.get('logical_source')}, is_midi={is_midi_topic or is_midi_source}", "DEBUG")

        if is_midi_topic or is_midi_source:
            meta = message.get("meta", {})
            value = message.get("value")
            is_tx = message.get("logical_source") == "MIDI-TX" or meta.get("midi_raw") is not None
            direction = "TX" if is_tx else "RX"
            
            if isinstance(meta, dict) and "raw" in meta:
                self.on_midi_activity(direction, meta)
            elif isinstance(value, dict) and "raw" in value:
                self.on_midi_activity(direction, value)
            elif is_midi_topic:
                real_val = value.get("value") if isinstance(value, dict) else value
                import re
                note_match = re.search(r"note(\d+)", topic)
                note = int(note_match.group(1)) if note_match else 0
                ch_match = re.search(r"ch(\d+)", topic)
                channel = (int(ch_match.group(1)) - 1) if ch_match else 0
                
                m_type = "note_on" if real_val > 0 else "note_off"
                self.on_midi_activity(direction, {
                    "value": real_val, 
                    "topic": topic,
                    "note": note,
                    "channel": channel,
                    "velocity": real_val if real_val <= 127 else 127,
                    "type": m_type,
                    "raw": f"{m_type} note={note} channel={channel} velocity={real_val}"
                })

    def on_midi_activity(self, direction, message):
        """Called when MIDI traffic occurs."""
        try:
            # ⚡ Robustness: Ensure we pass current values, not late-binding closures
            self.after(0, lambda d=direction, m=message: self._process_activity(d, m))
        except tk.TclError:
            pass # App is closing

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")

        # 1. Header & Hardware Search
        header_frame = tk.Frame(self, bg="#2b2b2b")
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))
        tk.Label(header_frame, text="🎹 MIDI CONTROLLER HUB", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        self.hw_search = MidiHardwareSearch(header_frame, refresh_callback=self._refresh_ui)
        self.hw_search.pack(side=tk.RIGHT, padx=20)

        # ⚡ NEW: Keyboard Visualizer at the TOP (as requested)
        kb_frame = tk.LabelFrame(self, text="Keyboard Visualizer (C1-C7)", bg="#2b2b2b", fg="#888888")
        kb_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)
        self.keyboard = MidiKeyboard(kb_frame, height=80) 
        self.keyboard.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # 2. Main Content Area
        content_pane = tk.Frame(self, bg="#2b2b2b")
        content_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Column: Hardware & Connections
        left_col = tk.Frame(content_pane, bg="#2b2b2b", width=300)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5)

        hw_frame = tk.LabelFrame(left_col, text="Detected Ports", bg="#2b2b2b", fg="#888888")
        hw_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        self.midi_hardware = MidiHardware(hw_frame)
        self.midi_hardware.pack(fill=tk.BOTH, expand=True)

        conn_frame = tk.LabelFrame(left_col, text="Active Connections", bg="#2b2b2b", fg="#888888")
        conn_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        self.conn_mgr = MidiConnectionManager(conn_frame)
        self.conn_mgr.pack(fill=tk.BOTH, expand=True)

        # Right Column: Feed Only (Visualizer moved to top)
        right_col = tk.Frame(content_pane, bg="#2b2b2b")
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        feed_frame = tk.LabelFrame(right_col, text="Live MIDI Feed", bg="#2b2b2b", fg="#888888")
        feed_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        self.midi_feed = MidiFeed(feed_frame)
        self.midi_feed.pack(fill=tk.BOTH, expand=True)

    def _refresh_ui(self):
        if not self.midi_manager: return
        info = self.midi_manager.get_port_info()
        self.midi_hardware.update_ports(info)
        self.conn_mgr.update_connections(info)

    def _process_activity(self, direction, message):
        matrix_log("comms", "midi", "_process_activity", f"🎹 [DASH] Processing activity: {direction} {message}", "DEBUG")
        # ⚡ CRITICAL: The visualizer needs the full message (dict or object)
        self.keyboard.handle_midi(message)
        
        channel = 0
        message_str = ""
        
        if isinstance(message, dict):
            channel = message.get("channel", 0)
            message_str = message.get("raw", str(message))
            # Fallback for topic-only messages
            if not message_str and message.get("topic"):
                message_str = f"{message.get('type', 'event')} on {message.get('topic')}"
        elif hasattr(message, "channel"):
            channel = message.channel
            message_str = str(message)
        else:
            message_str = str(message)
            
        self.midi_feed.add_log(direction, message_str, channel)

    def destroy(self):
        if self.midi_manager:
            try: self.midi_manager.remove_monitor_callback(self.on_midi_activity)
            except: pass
        else:
            try:
                from oaComBroker.Core.protocol_router.manager import ProtocolRouter
                ProtocolRouter.get_instance().unregister_cache_observer(self._on_protocol_event)
            except: pass
        super().destroy()

def get_gui_class():
    return MidiDashboard
