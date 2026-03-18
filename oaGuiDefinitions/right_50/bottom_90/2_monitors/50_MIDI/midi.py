import tkinter as tk
from tkinter import ttk
import datetime
from oaGuiElements.utils.midi_keyboard.midi_keyboard import MidiKeyboard, get_midi_color

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
            # Add a local callback for the dashboard monitor
            self.midi_manager.add_monitor_callback(self.on_midi_activity)
            self._refresh_ui()

    def _find_midi_manager(self, widget):
        from oaGuiBuilder.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder) and hasattr(curr, 'app_instance'):
                return getattr(curr.app_instance, 'midi_manager', None)
            try:
                curr = curr.master
            except Exception as e:
                logger.trace(f"End of widget tree reached: {e}")
                break
        return None

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="🎹 MIDI CONTROLLER HUB", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        ttk.Button(header, text="Refresh Dashboard", command=self._refresh_ui).pack(side=tk.RIGHT, padx=20)

        # 2. Main Layout (Vertical Stack: Keyboard, Monitor then Ports)
        main_pane = tk.Frame(self, bg="#2b2b2b")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10)

        # --- TOP: Keyboard Visualizer ---
        kb_frame = tk.LabelFrame(main_pane, text="Keyboard Visualizer (6 Octaves)", bg="#2b2b2b", fg="#888888")
        kb_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.keyboard = MidiKeyboard(kb_frame, height=80)
        self.keyboard.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # --- MIDDLE: Live Monitor ---
        log_frame = tk.LabelFrame(main_pane, text="Live MIDI Feed (Monitor)", bg="#2b2b2b", fg="#888888")
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, bg="#000000", fg="#ff00ff", font=("Courier", 10), height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- BOTTOM: Ports List ---
        port_frame = tk.LabelFrame(main_pane, text="Detected Hardware Ports", bg="#2b2b2b", fg="#888888")
        port_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=5, pady=5)

        self.port_tree = ttk.Treeview(port_frame, columns=("Type", "Status"), show="tree headings", height=6)
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
            self.port_tree.insert("", "end", text="HELP", values=("FIX", "Check terminal or run Setup.py"))
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
        # 1. Update Keyboard
        self.keyboard.handle_midi(msg)
        
        # 2. Add to Log
        channel = 0
        if isinstance(msg, dict):
            # Try pre-parsed channel first
            channel = msg.get("channel")
            if channel is None:
                # Fallback: Parse from raw string
                raw = msg.get("raw", "")
                if "channel=" in raw:
                    try:
                        channel = int(raw.split("channel=")[1].split()[0])
                    except Exception as e:
                        logger.debug(f"Failed to parse MIDI channel from raw string: {e}")
                        channel = 0
                else:
                    channel = 0
        elif hasattr(msg, "channel"):
            channel = msg.channel
            
        msg_str = str(msg.get("raw") if isinstance(msg, dict) else msg)
        self._add_log(direction, msg_str, channel or 0)

    def _add_log(self, direction, msg_str, channel=0):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        color = get_midi_color(channel)
        
        # Create or reuse a tag for this specific color
        tag_name = f"ch_color_{color.replace('#', '')}"
        self.log_text.tag_configure(tag_name, foreground=color)
        
        self.log_text.insert("1.0", f"[{ts}] {direction} >> {msg_str}\n", tag_name)
        # Truncate
        if int(self.log_text.index('end-1c').split('.')[0]) > 100:
            self.log_text.delete('100.0', tk.END)

    def destroy(self):
        if self.midi_manager:
            try:
                self.midi_manager.remove_monitor_callback(self.on_midi_activity)
            except Exception as e:
                logger.trace(f"Failed to remove MIDI monitor callback: {e}")
        super().destroy()

def get_gui_class():
    return MidiDashboard
