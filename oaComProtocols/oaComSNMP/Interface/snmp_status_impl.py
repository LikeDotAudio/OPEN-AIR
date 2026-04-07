# oaComProtocols.oaComSNMP/Interface/snmp_status_impl.py
# Author: Anthony Peter Kuzub
# Version: 20260405.1130.2
#
# Description: Passive SNMP Status Display Implementation.

import tkinter as tk
from tkinter import ttk
import json
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

class SnmpStatusImplementation(tk.Frame, TransparencyMixin):
    """
    Passive SNMP Status & Installer Interface Implementation.
    Observes CORE status via MQTT and sends control commands.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        
        # ⚡ DEPENDENCY INJECTION: Prioritize injected config
        self.mqtt_client = self.config_data.get("mqtt_connection_manager")
        self.subscriber_router = self.config_data.get("subscriber_router")
        
        if not self.mqtt_client or not self.subscriber_router:
            self.mqtt_client, self.subscriber_router = self._find_mqtt_services(parent)
        
        self._flash_state = False
        self._is_offline = True
        self._last_status = {}
        
        self._setup_ui()
        
        if self.subscriber_router:
            # Subscribe to SNMP bridge status updates from CORE
            self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Status/SNMP/Bridge", self._on_status_received)
            # Initial request for a script generate to populate UI
            self.refresh_script()

    def _find_mqtt_services(self, widget):
        from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder) and hasattr(curr, 'app_instance'):
                app = curr.app_instance
                mqtt_conn = getattr(app, 'mqtt_connection_manager', None)
                sub_router = getattr(app, 'subscriber_router', None)
                return mqtt_conn, sub_router
            try: curr = curr.master
            except: break
        return None, None

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="🌐 SNMP BRIDGE (REMOTE STATUS)", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        # ⚡ VISIBILITY: Use a more contrasting color for the setup button
        self.re_setup_btn = tk.Button(
            header, 
            text="⚠️ RE-SETUP BRIDGE", 
            command=self.refresh_script,
            font=("Helvetica", 10, "bold"),
            bg="#ffaa00",
            fg="#000000",
            activebackground="#ffcc00",
            padx=15,
            bd=1,
            relief="raised"
        )
        self.re_setup_btn.pack(side=tk.RIGHT, padx=20)

        # 2. Split View (Status + Installer)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Bridge Diagnostics ---
        diag_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(diag_frame, weight=1)

        self.tree = ttk.Treeview(diag_frame, columns=("Value"), show="tree", height=6)
        self.tree.heading("#0", text="Property")
        self.tree.column("#0", width=250)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- BOTTOM: Installer Tool ---
        install_frame = tk.LabelFrame(self.paned, text="Linux SNMP Installer Script (Automated Setup)", bg="#2b2b2b", fg="#888888")
        self.paned.add(install_frame, weight=2)

        # Tool buttons
        tool_bar = tk.Frame(install_frame, bg="#2b2b2b")
        tool_bar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        ttk.Button(tool_bar, text="Request Script", command=self.refresh_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(tool_bar, text="Copy to Clipboard", command=self.copy_script).pack(side=tk.LEFT, padx=5)
        tk.Label(tool_bar, text="Paste this into your Linux Terminal", font=("Courier", 9), fg="#666666", bg="#2b2b2b").pack(side=tk.RIGHT, padx=10)

        # Script area
        self.text_area = tk.Text(install_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), padx=10, pady=10, bd=0)
        scroll = ttk.Scrollbar(install_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scroll.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_status_received(self, msg):
        """Callback for MQTT status updates from CORE."""
        payload = msg.payload
        if not isinstance(payload, dict):
            try:
                import json
                payload = json.loads(payload)
            except:
                return

        self._last_status = payload
        # Use .after() to update UI from MQTT thread safely
        self.after(0, self._refresh_ui)

    def _refresh_ui(self):
        """Update diagnostics from the last received MQTT status."""
        status = self._last_status
        if not status: return
        
        # ⚡ HEALTH CHECK: Only show offline if it's explicitly not running.
        is_running = status.get("running", False)
        self._is_offline = not is_running
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.tree.insert("", "end", text="Bridge Status", values=("ACTIVE" if is_running else "OFFLINE",))
        self.tree.insert("", "end", text="Socket Address", values=(status.get("socket", "Unknown"),))
        self.tree.insert("", "end", text="Root OID", values=(status.get("base_oid", "Unknown"),))
        self.tree.insert("", "end", text="Variables Active", values=(status.get("object_count", 0),))
        self.tree.insert("", "end", text="Operating Mode", values=("MASTER HUB" if status.get("bridge_mode") == True else "OBSERVER ONLY",))
        self.tree.insert("", "end", text="Active MIB", values=(status.get("mib_path", "Unknown"),))

        # Update script area if provided in the status message
        if "installer_script" in status:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", status["installer_script"])
            self.text_area.see("1.0")

    def refresh_script(self):
        """Sends a command to CORE to regenerate and publish the installer script."""
        if self.mqtt_client:
            self.mqtt_client.publish("OPEN-AIR/System/Control/SNMP/GenerateScript", {"request": "generate"})

    def copy_script(self):
        content = self.text_area.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)

    def render(self):
        self.configure(bg=self.cget("bg"))

__all__ = ["SnmpStatusImplementation"]
