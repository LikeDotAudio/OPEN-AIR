import sys
from pathlib import Path

# 1. Setup Environment
current_path = Path(__file__).resolve()
root_path = current_path
for parent in current_path.parents:
    if (parent / "oaComBroker").exists() and (parent / "oaGui/Assets").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import datetime
import inspect

# 44_REST/gui_REST.py
# Author: Anthony Peter Kuzub
# Version: 20260414.0020.1
#
# Description: Advanced REST API Monitor & Control Hub.
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk

import oaComProtocols.oaComREST.Entry as REST_MODULE

# --- Standard Debug Logging Setup ---
from oaLogging.Entry import logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGui.Core.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass

class RestDashboard(tk.Frame, TransparencyMixin):
    """
    REST API Status, Control & Monitor.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        self._destroyed = False

        super().__init__(parent, **kwargs)

        self._setup_ui()

        # --- Standalone Initialization ---
        try:
            state_cache = self.config_data.get("state_cache_manager")
            protocol_router = self.config_data.get("protocol_router")

            REST_MODULE.get_manager(state_cache_manager=state_cache, protocol_router=protocol_router)
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🌐 RestDashboard: RESTManager linked successfully.", "INFO")
        except Exception as e:
            logger.error(f"🌐 RestDashboard: Standalone setup failed: {e}")

        # Register for activity callbacks
        try:
            REST_MODULE.add_monitor_callback(self.on_rest_activity)
        except Exception as e:
            logger.error(f"RestDashboard: Failed to register callback: {e}")

        self._refresh_ui()
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedules a periodic status check."""
        self._refresh_ui()
        if not self._destroyed:
            self.after(2000, self._schedule_refresh)

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))

        tk.Label(header, text="🌐 REST API CONTROL HUB", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)

        self.status_lbl = tk.Label(header, text="Status: LOADING...", font=("Courier", 10, "bold"), fg="#ffff00", bg="#2b2b2b")
        self.status_lbl.pack(side=tk.RIGHT, padx=20)

        # 2. Control Bar
        ctrl_bar = tk.Frame(self, bg="#333333", height=40)
        ctrl_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.btn_explorer = tk.Button(ctrl_bar, text="🔭 EXPLORER", bg="#1a3a4a", fg="#ffffff", font=("Helvetica", 9, "bold"),
                                     command=self._open_explorer, width=12, relief="raised", bd=2)
        self.btn_explorer.pack(side=tk.RIGHT, padx=5, pady=5)

        self.btn_browser = tk.Button(ctrl_bar, text="🌍 API DOCS", bg="#333344", fg="#ffffff", font=("Helvetica", 9, "bold"),
                                    command=self._open_browser, width=12, relief="raised", bd=2)
        self.btn_browser.pack(side=tk.RIGHT, padx=5, pady=5)

        # 3. Split View (Monitor + Info)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Live Traffic Monitor ---
        monitor_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(monitor_frame, weight=3)

        tk.Label(monitor_frame, text="📡 LIVE TRAFFIC", font=("Helvetica", 8, "bold"), fg="#888888", bg="#2b2b2b").pack(anchor="w")

        cols = ("Time", "Method", "Path", "Status", "Payload")
        self.tree = ttk.Treeview(monitor_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")

        self.tree.column("Time", width=100)
        self.tree.column("Method", width=80)
        self.tree.column("Path", width=250, anchor="w")
        self.tree.column("Status", width=80)
        self.tree.column("Payload", width=200, anchor="w")

        # Tags for status codes
        self.tree.tag_configure("2xx", foreground="#00ff00")
        self.tree.tag_configure("4xx", foreground="#ffaa00")
        self.tree.tag_configure("5xx", foreground="#ff0000")

        vsb = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # --- BOTTOM: Routes & Status ---
        info_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(info_frame, weight=4)

        tabs = ttk.Notebook(info_frame)
        tabs.pack(fill=tk.BOTH, expand=True)

        self.routes_frame = tk.Frame(tabs, bg="#1a1a1a")
        tabs.add(self.routes_frame, text=" API ROUTES ")

        self.routes_tree = ttk.Treeview(self.routes_frame, columns=("Methods"), show="tree headings", height=5)
        self.routes_tree.heading("#0", text="Endpoint Path")
        self.routes_tree.heading("Methods", text="Allowed Methods")
        self.routes_tree.column("#0", width=300)
        self.routes_tree.column("Methods", width=150)
        self.routes_tree.pack(fill=tk.BOTH, expand=True)

        # 4. Footer Info / Network Status
        status_frame = tk.LabelFrame(self, text="Network & Routing Status", bg="#2b2b2b", fg="#888888")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False, padx=15, pady=(5, 10))

        self.info_tree = ttk.Treeview(status_frame, columns=("Value"), show="tree", height=4)
        self.info_tree.heading("#0", text="Property")
        self.info_tree.column("#0", width=200)
        self.info_tree.pack(fill=tk.X, expand=True, padx=5, pady=5)

        self.footer_lbl = tk.Label(self, text="Server URL: -", bg="#2b2b2b", fg="#888888", font=("Helvetica", 8))
        self.footer_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=2)

    def _open_browser(self):
        status = REST_MODULE.get_status()
        if status.get("docs_url"):
            webbrowser.open(status["docs_url"])

    def _open_explorer(self):
        status = REST_MODULE.get_status()
        if status.get("url"):
            webbrowser.open(status["url"])

    def _refresh_ui(self):
        status = REST_MODULE.get_status()

        if status.get("running"):
            self.status_lbl.configure(text=f"🟢 ONLINE | PORT: {status['port']}", fg="#00ff00")
            self.footer_lbl.configure(text=f"Server URL: {status['url']} (Swagger Docs: {status['docs_url']})")
        else:
            self.status_lbl.configure(text="🔴 OFFLINE", fg="#ff4444")
            self.footer_lbl.configure(text="Server URL: OFFLINE")

        # Update Detail Tree
        for item in self.routes_tree.get_children():
            self.routes_tree.delete(item)

        for route in status.get("routes", []):
            self.routes_tree.insert("", "end", text=route["path"], values=(", ".join(route["methods"]),))

        # Update Network Status (Footer section)
        for item in self.info_tree.get_children():
            self.info_tree.delete(item)

        self.info_tree.insert("", "end", text="Listening Host", values=(status["host"],))
        self.info_tree.insert("", "end", text="REST Port", values=(status["port"],))
        self.info_tree.insert("", "end", text="Service Status", values=("Running" if status["running"] else "Stopped",))
        self.info_tree.insert("", "end", text="Initialization", values=("Success" if status["initialized"] else "Failed",))

    def on_rest_activity(self, method, path, status_code, payload=None):
        """Callback for real-time traffic."""
        self.after(0, lambda: self._add_log_entry(method, path, status_code, payload))

    def _add_log_entry(self, method, path, status_code, payload=None):
        if self._destroyed: return
        now = datetime.datetime.now()
        timestamp = now.strftime("%H:%M:%S.%f")[:-3]

        tag = "2xx"
        if 400 <= status_code < 500: tag = "4xx"
        elif status_code >= 500: tag = "5xx"

        display_payload = str(payload) if payload else "-"
        self.tree.insert("", 0, values=(timestamp, method, path, status_code, display_payload), tags=(tag,))

        if len(self.tree.get_children()) > 50:
            self.tree.delete(self.tree.get_children()[-1])

    def render(self): pass

    def destroy(self):
        self._destroyed = True
        try:
            REST_MODULE.remove_monitor_callback(self.on_rest_activity)
        except Exception: pass
        super().destroy()

def get_gui_class():
    return RestDashboard
