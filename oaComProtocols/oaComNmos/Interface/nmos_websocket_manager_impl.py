# oaComProtocols.oaComNmos/Interface/nmos_websocket_manager_impl.py
# Author: Gemini (Collaborator)
# Version: 20260414.0020.1
#
# Description: NMOS WebSocket Manager Implementation.
# Provides controls to start/stop the IS-07 WebSocket transport.

import tkinter as tk
from tkinter import ttk
import threading
import time
from oaLogging.Methods.matrix_gate import matrix_log

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass

class NmosWebsocketManagerImplementation(tk.Frame, TransparencyMixin):
    """
    NMOS WebSocket Manager GUI.
    Allows users to control the IS-07 WebSocket transport.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}
        self.global_state = self.config.get("global_state", {})
        
        # ⚡ MANDATE: NMOS WebSocket must ALWAYS be online.
        self.is_connected = False
        self.ws_url = "ws://localhost:8080/is07"
        self.client_count = 0
        
        self._setup_ui()
        self._start_monitor_thread()

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        bg_color = self.cget("bg") or "#2b2b2b"
        self.configure(bg=bg_color)

        # 1. Header
        header = tk.Frame(self, bg=bg_color)
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="🔌 NMOS IS-07 WEBSOCKET MANAGER", font=("Helvetica", 14, "bold"), fg="#ffffff", bg=bg_color).pack(side=tk.LEFT, padx=20)

        # 2. Status Panel
        status_frame = tk.LabelFrame(self, text=" WebSocket Status ", bg=bg_color, fg="#888888", padx=10, pady=10)
        status_frame.pack(fill=tk.X, padx=20, pady=10)

        self.ws_status_var = tk.StringVar(value="Status: RUNNING")
        self.ws_status_lbl = tk.Label(status_frame, textvariable=self.ws_status_var, font=("Helvetica", 12, "bold"), fg="#00ff00", bg=bg_color)
        self.ws_status_lbl.pack(side=tk.LEFT, padx=10)

        self.ws_info_var = tk.StringVar(value=f"URL: {self.ws_url} | Clients: {self.client_count}")
        tk.Label(status_frame, textvariable=self.ws_info_var, font=("Courier", 10), fg="#aaaaaa", bg=bg_color).pack(side=tk.RIGHT, padx=10)

        # 3. Controls
        ctrl_frame = tk.Frame(self, bg=bg_color)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
        
        self.start_btn = ttk.Button(ctrl_frame, text="RESTART WEBSOCKET", command=self._start_ws)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        # ⚡ MANDATE: WS must be ALWAYS online. Removing STOP button to prevent accidental downtime.
        # self.stop_btn = ttk.Button(ctrl_frame, text="STOP WEBSOCKET", command=self._stop_ws)
        # self.stop_btn.pack(side=tk.LEFT, padx=5)

    def _start_monitor_thread(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _monitor_loop(self):
        while self.running:
            try:
                # Check bridge status
                bridge = self.global_state.get("BRIDGE")
                if bridge:
                    self.is_connected = bridge.is_running
                    # In a real impl we'd check active clients from the transport
                    self.client_count = 1 if bridge.is_running else 0
                
                if self.winfo_exists():
                    self.after(0, self._refresh_ui)
            except (RuntimeError, tk.TclError):
                # Main loop not running or widget destroyed
                break
            except Exception as e:
                matrix_log("ui", "nmos", "ws_monitor_error", f"Error in WS monitor: {e}", "ERROR")
            
            time.sleep(2)

    def _refresh_ui(self):
        status_text = "Status: RUNNING" if self.is_connected else "Status: STOPPED"
        status_color = "#00ff00" if self.is_connected else "#ff0000"
        
        self.ws_status_var.set(status_text)
        self.ws_status_lbl.config(fg=status_color)
        
        url = self.ws_url if self.is_connected else "-"
        clients = self.client_count if self.is_connected else 0
        self.ws_info_var.set(f"URL: {url} | Clients: {clients}")

    def _start_ws(self):
        matrix_log("ui", "nmos", "start_ws", "Starting IS-07 WebSocket transport...", "INFO")
        bridge = self.global_state.get("BRIDGE")
        if bridge:
            bridge.start()
        self._refresh_ui()

    def _stop_ws(self):
        matrix_log("ui", "nmos", "stop_ws", "Stopping IS-07 WebSocket transport...", "WARNING")
        bridge = self.global_state.get("BRIDGE")
        if bridge:
            bridge.stop()
        self._refresh_ui()

    def render(self):
        self.configure(bg=self.cget("bg"))

    def destroy(self):
        self.running = False
        super().destroy()

__all__ = ["NmosWebsocketManagerImplementation"]
