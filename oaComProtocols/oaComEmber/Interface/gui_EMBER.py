# /home/anthony/Documents/OPEN-AIR/oaComProtocols.oaComEmber/Interface/gui_EMBER.py
# Author: Gemini (Collaborator)
# Version: 20260407.1100.1
#
# Description: Advanced Ember+ Monitor & Control Hub.
# This file contains the primary implementation logic for the Ember+ GUI.

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

# --- Path Guard: Ensure project root is in sys.path ---
current_path = Path(__file__).resolve()
root_path = current_path
for parent in current_path.parents:
    if (parent / "oaComBroker").exists() and (parent / "oaGui/Assets").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log

try:
    import oaComProtocols.oaComEmber.Entry as EMBER_MODULE
except ImportError:
    EMBER_MODULE = None

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass

class EmberDashboardImplementation(tk.Frame, TransparencyMixin):
    """
    Ember+ Status, Control & Monitor.
    Manages the Ember+ connection lifecycle and provides deep inspection of tree activity.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)

        super().__init__(parent, **kwargs)

        # Activity cache for investigation
        self._activity_cache = {}

        self._setup_ui()

        # --- Standalone Initialization ---
        if EMBER_MODULE and hasattr(EMBER_MODULE, "get_manager"):
            try:
                mqtt_conn = self.config_data.get("mqtt_connection_manager") or (getattr(self.config_data.get("app_instance"), "mqtt_connection_manager", None) if self.config_data.get("app_instance") else None)

                EMBER_MODULE.get_manager(mqtt_connection_manager=mqtt_conn)
                matrix_log("core", "system", "EmberDashboard", "🧬 EmberDashboard: EmberManager linked successfully.", "INFO")
            except Exception as e:
                logger.error(f"🧬 EmberDashboard: Standalone setup failed: {e}")

        # Register for activity callbacks
        if EMBER_MODULE and hasattr(EMBER_MODULE, "add_monitor_callback"):
            try:
                EMBER_MODULE.add_monitor_callback(self.on_ember_activity)
            except Exception as e:
                logger.error(f"EmberDashboard: Failed to register callback: {e}")

        self._refresh_ui()
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedules a periodic status check."""
        self._refresh_ui()
        if not getattr(self, '_destroyed', False):
            self.after(2000, self._schedule_refresh)

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))

        tk.Label(header, text="🧬 EMBER+ CONTROL HUB", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)

        self.status_lbl = tk.Label(header, text="Status: LOADING...", font=("Courier", 10, "bold"), fg="#ffff00", bg="#2b2b2b")
        self.status_lbl.pack(side=tk.RIGHT, padx=20)

        # 2. Control Bar (with input as requested)
        ctrl_bar = tk.Frame(self, bg="#333333", height=40)
        ctrl_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(ctrl_bar, text="TARGET IP:", font=("Helvetica", 8, "bold"), fg="#888888", bg="#333333").pack(side=tk.LEFT, padx=(10, 2))
        self.ip_entry = tk.Entry(ctrl_bar, bg="#000000", fg="#00ff00", insertbackground="white", width=15, bd=1, relief="flat")
        self.ip_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.ip_entry.insert(0, "127.0.0.1")

        tk.Label(ctrl_bar, text="PORT:", font=("Helvetica", 8, "bold"), fg="#888888", bg="#333333").pack(side=tk.LEFT, padx=(10, 2))
        self.port_entry = tk.Entry(ctrl_bar, bg="#000000", fg="#00ff00", insertbackground="white", width=6, bd=1, relief="flat")
        self.port_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.port_entry.insert(0, "9000")

        self.btn_connect = tk.Button(ctrl_bar, text="CONNECT", bg="#1a4a1a", fg="#ffffff", font=("Helvetica", 8, "bold"),
                                    command=self._on_connect, relief="raised", bd=2)
        self.btn_connect.pack(side=tk.LEFT, padx=10)

        # 3. Split View (Monitor + Dissector)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Live Tree Monitor ---
        monitor_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(monitor_frame, weight=3)

        cols = ("Time", "Dir", "Path", "Value", "Type")
        self.tree = ttk.Treeview(monitor_frame, columns=cols, show="headings", style="SMPTE.Treeview")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        self.tree.column("Time", width=120)
        self.tree.column("Path", width=250, anchor="w")
        self.tree.column("Value", width=150)
        self.tree.column("Type", width=100)

        self.tree.tag_configure("RX", foreground="#00ffff")   # Cyan
        self.tree.tag_configure("TX", foreground="#ffff00")   # Yellow

        vsb = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_node)

        # --- BOTTOM: Dissector ---
        inspect_frame = tk.Frame(self.paned, bg="#000000", bd=1, relief="sunken")
        self.paned.add(inspect_frame, weight=2)

        inspect_header = tk.Frame(inspect_frame, bg="#1a1a1a")
        inspect_header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(inspect_header, text="🔍 EMBER+ NODE DISSECTOR", font=("Helvetica", 10, "bold"), fg="#888888", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        tk.Button(inspect_header, text="CLEAR", bg="#333333", fg="#ffffff", font=("Helvetica", 7),
                  command=self._clear_monitor, bd=1).pack(side=tk.RIGHT, padx=5, pady=2)

        self.inspect_text = tk.Text(inspect_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), bd=0, highlightthickness=0)
        self.inspect_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _on_connect(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        if EMBER_MODULE and hasattr(EMBER_MODULE, "connect"):
            EMBER_MODULE.connect(ip, int(port))
        logger.info(f"Ember+ Attempting connection to {ip}:{port}")

    def _clear_monitor(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._activity_cache.clear()
        self.inspect_text.delete("1.0", tk.END)

    def _refresh_ui(self):
        if not EMBER_MODULE or not hasattr(EMBER_MODULE, "status"):
            self.status_lbl.configure(text="OFFLINE (No Module)", fg="#ff4444")
            return

        try:
            status = EMBER_MODULE.status()
        except Exception:
            self.status_lbl.configure(text="ERROR", fg="#ff0000")
            return

        if isinstance(status, dict):
            is_running = status.get("running", False)
            conn_str = status.get("connection", "DISCONNECTED")
        else:
            is_running = status == "active"
            conn_str = status

        if is_running:
            self.status_lbl.configure(text=f"ACTIVE: {conn_str}", fg="#00ff00")
        else:
            self.status_lbl.configure(text=f"STATUS: {conn_str}", fg="#ffff00")

    def on_ember_activity(self, direction, path, value, node_type=None):
        self.after(0, lambda: self._add_log_entry(direction, path, value, node_type))

    def _add_log_entry(self, direction, path, value, node_type):
        now = datetime.datetime.now()
        timestamp = now.strftime("%H:%M:%S.%f")[:-3]

        item_id = self.tree.insert("", 0, values=(timestamp, direction, path, value, node_type or "-"), tags=(direction,))

        self._activity_cache[timestamp] = {
            "timestamp": timestamp,
            "direction": direction,
            "path": path,
            "value": value,
            "type": node_type
        }

        if len(self.tree.get_children()) > 100:
            last_item = self.tree.get_children()[-1]
            last_ts = self.tree.item(last_item)["values"][0]
            if last_ts in self._activity_cache: del self._activity_cache[last_ts]
            self.tree.delete(last_item)

    def on_select_node(self, event):
        selected = self.tree.selection()
        if not selected: return

        item = self.tree.item(selected[0])
        timestamp = item["values"][0]
        data = self._activity_cache.get(timestamp)
        if not data: return

        self.inspect_text.delete("1.0", tk.END)
        self.inspect_text.insert(tk.END, f"TIME     : {data['timestamp']}\n")
        self.inspect_text.insert(tk.END, f"DIR      : {data['direction']}\n")
        self.inspect_text.insert(tk.END, f"PATH     : {data['path']}\n")
        self.inspect_text.insert(tk.END, f"VALUE    : {data['value']}\n")
        self.inspect_text.insert(tk.END, f"TYPE     : {data['type']}\n")

    def render(self): pass

    def destroy(self):
        self._destroyed = True
        if EMBER_MODULE and hasattr(EMBER_MODULE, "remove_monitor_callback"):
            try: EMBER_MODULE.remove_monitor_callback(self.on_ember_activity)
            except: pass
        super().destroy()
