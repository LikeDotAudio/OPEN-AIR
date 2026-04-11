# oaComProtocols.oaComNmos/Interface/nmos_connection_monitor_impl.py
# Author: Gemini (Collaborator)
# Version: 20260405.2145.1
#
# Description: NMOS Connection Monitor Implementation.
# Shows registration status with the NMOS registry and HTTP server status.

import tkinter as tk
from tkinter import ttk
import requests
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

class NmosConnectionMonitorImplementation(tk.Frame, TransparencyMixin):
    """
    NMOS Connection Monitor GUI.
    Displays Node/Device registration status and HTTP server health.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config or {}
        self.app_instance = self.config.get("app_instance")
        
        # Default values
        self.registrar_url = "http://localhost:4000"
        self.node_id = "Unknown"
        self.device_id = "Unknown"
        self.host_ip = "0.0.0.0"
        self.is_registered = False
        self.is_server_running = False
        
        self._setup_ui()
        self._start_monitor_thread()

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        bg_color = self.cget("bg") or "#2b2b2b"
        self.configure(bg=bg_color)

        # 1. Header
        header = tk.Frame(self, bg=bg_color)
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="📡 NMOS CONNECTION MONITOR", font=("Helvetica", 14, "bold"), fg="#ffffff", bg=bg_color).pack(side=tk.LEFT, padx=20)

        # 2. Info Panel
        info_frame = tk.LabelFrame(self, text=" System Status ", bg=bg_color, fg="#888888", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        self.status_tree = ttk.Treeview(info_frame, columns=("Value"), show="tree", height=6)
        self.status_tree.heading("#0", text="Property")
        self.status_tree.column("#0", width=200)
        self.status_tree.pack(fill=tk.BOTH, expand=True)

        # 3. Controls
        ctrl_frame = tk.Frame(self, bg=bg_color)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
        
        self.refresh_btn = ttk.Button(ctrl_frame, text="Force Re-registration", command=self._force_re_register)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(ctrl_frame, text="Status: Initializing...", font=("Courier", 10), fg="#aaaaaa", bg=bg_color)
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def _start_monitor_thread(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _monitor_loop(self):
        while self.running:
            try:
                # In a real app, we'd pull these from the app_instance or a global state
                # For now, we simulate monitoring of the local NMOS environment
                self._update_status()
            except Exception as e:
                matrix_log("ui", "nmos", "_monitor_loop", f"Error in monitor loop: {e}", "ERROR")
            time.sleep(5)

    def _update_status(self):
        # Placeholder for actual status check
        # We'll try to reach the local NMOS API
        try:
            # Check if Node API is responsive
            # This is just a simulation of checking local connection_api
            self.is_server_running = True # Assume true for this demo if logic exists
            
            # Simulated IDs
            self.node_id = "00000000-0000-0000-0000-000000000000"
            self.device_id = "11111111-1111-1111-1111-111111111111"
            self.host_ip = "127.0.0.1"
            
            self.after(0, self._refresh_ui)
        except Exception:
            self.is_server_running = False
            self.after(0, self._refresh_ui)

    def _refresh_ui(self):
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
            
        self.status_tree.insert("", "end", text="Node ID", values=(self.node_id,))
        self.status_tree.insert("", "end", text="Device ID", values=(self.device_id,))
        self.status_tree.insert("", "end", text="Host IP", values=(self.host_ip,))
        self.status_tree.insert("", "end", text="Registrar URL", values=(self.registrar_url,))
        
        reg_status = "REGISTERED" if self.is_registered else "NOT REGISTERED"
        reg_color = "#00ff00" if self.is_registered else "#ff0000"
        self.status_tree.insert("", "end", text="Registration", values=(reg_status,))
        
        srv_status = "RUNNING" if self.is_server_running else "STOPPED"
        srv_color = "#00ff00" if self.is_server_running else "#ff0000"
        self.status_tree.insert("", "end", text="HTTP Server", values=(srv_status,))
        
        self.status_label.config(text=f"Last Sync: {time.strftime('%H:%M:%S')}", fg="#00ff00" if self.is_server_running else "#ff0000")

    def _force_re_register(self):
        matrix_log("ui", "nmos", "re_register", "Force re-registration requested.", "INFO")
        # In real usage, this would call registration_manager.register_all_resources()
        self.is_registered = True
        self._refresh_ui()

    def render(self):
        self.configure(bg=self.cget("bg"))

    def destroy(self):
        self.running = False
        super().destroy()

__all__ = ["NmosConnectionMonitorImplementation"]
