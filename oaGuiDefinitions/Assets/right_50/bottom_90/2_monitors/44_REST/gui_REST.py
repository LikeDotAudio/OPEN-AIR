# 44_REST/gui_REST.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1300.1
#
# Description: Advanced REST API Monitor & Control Hub.
# Provides service management, route inspection, and live traffic logging.

import tkinter as tk
from tkinter import ttk
import datetime
import sys
import webbrowser
from pathlib import Path

# --- Path Guard: Ensure project root is in sys.path ---
current_path = Path(__file__).resolve()
root_path = current_path
for parent in current_path.parents:
    if (parent / "oaComBroker").exists() and (parent / "oaGuiDefinitions").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import oaComREST.Entry as REST_MODULE

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Entry import logger
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

class RestDashboard(tk.Frame, TransparencyMixin):
    """
    REST API Status, Control & Monitor.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        
        self._setup_ui()
        
        # --- Standalone Initialization ---
        try:
            state_cache = self.config_data.get("state_cache_manager")
            protocol_router = self.config_data.get("protocol_router") or \
                             (getattr(self.config_data.get("app_instance"), "protocol_router", None) if self.config_data.get("app_instance") else None)
            
            REST_MODULE.get_manager(state_cache_manager=state_cache, protocol_router=protocol_router)
            if LOCAL_DEBUG: logger.info("🌐 RestDashboard: RESTManager linked successfully.")
        except Exception as e:
            logger.error(f"🌐 RestDashboard: Standalone setup failed: {e}")

        # Register for activity callbacks
        try:
            REST_MODULE.add_monitor_callback(self.on_rest_activity)
        except Exception as e:
            logger.error(f"RestDashboard: Failed to register callback: {e}")
            
        self._refresh_ui()

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
        
        # Service Buttons
        self.btn_start = tk.Button(ctrl_bar, text="▶ START", bg="#1a4a1a", fg="#ffffff", font=("Helvetica", 9, "bold"), 
                                  command=self._start_service, width=10, relief="raised", bd=2)
        self.btn_start.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.btn_stop = tk.Button(ctrl_bar, text="🛑 STOP", bg="#4a1a1a", fg="#ffffff", font=("Helvetica", 9, "bold"), 
                                 command=self._stop_service, width=10, relief="raised", bd=2)
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_browser = tk.Button(ctrl_bar, text="🌍 OPEN API DOCS", bg="#333344", fg="#ffffff", font=("Helvetica", 9, "bold"), 
                                    command=self._open_browser, width=15, relief="raised", bd=2)
        self.btn_browser.pack(side=tk.RIGHT, padx=5, pady=5)

        # 3. Split View (Monitor + Info)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Live Traffic Monitor ---
        monitor_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(monitor_frame, weight=3)

        tk.Label(monitor_frame, text="📡 LIVE TRAFFIC", font=("Helvetica", 8, "bold"), fg="#888888", bg="#2b2b2b").pack(anchor="w")

        cols = ("Time", "Method", "Path", "Status")
        self.tree = ttk.Treeview(monitor_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        
        self.tree.column("Time", width=100)
        self.tree.column("Method", width=80)
        self.tree.column("Path", width=300, anchor="w")
        self.tree.column("Status", width=80)

        # Tags for status codes
        self.tree.tag_configure("2xx", foreground="#00ff00") # Green
        self.tree.tag_configure("4xx", foreground="#ffaa00") # Orange
        self.tree.tag_configure("5xx", foreground="#ff0000") # Red

        vsb = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # --- BOTTOM: Routes & Tutorial ---
        info_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(info_frame, weight=4)

        tabs = ttk.Notebook(info_frame)
        tabs.pack(fill=tk.BOTH, expand=True)

        # Tab 1: API Routes
        self.routes_frame = tk.Frame(tabs, bg="#1a1a1a")
        tabs.add(self.routes_frame, text=" API ROUTES ")
        
        self.routes_tree = ttk.Treeview(self.routes_frame, columns=("Methods"), show="tree headings", height=5)
        self.routes_tree.heading("#0", text="Endpoint Path")
        self.routes_tree.heading("Methods", text="Allowed Methods")
        self.routes_tree.column("#0", width=300)
        self.routes_tree.column("Methods", width=150)
        self.routes_tree.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Tutorial / Documentation
        tutorial_frame = tk.Frame(tabs, bg="#1a1a1a")
        tabs.add(tutorial_frame, text=" QUICK START GUIDE ")
        
        help_text = tk.Text(tutorial_frame, bg="#1a1a1a", fg="#cccccc", font=("Courier", 9), bd=0, padx=10, pady=10)
        help_text.pack(fill=tk.BOTH, expand=True)
        help_text.insert(tk.END, "OPEN-AIR REST API TUTORIAL\n", "bold")
        help_text.insert(tk.END, "==========================\n\n")
        help_text.insert(tk.END, "1. GETTING STATE:\n")
        help_text.insert(tk.END, "   GET /api/v1/state/PATH/TO/TOPIC\n")
        help_text.insert(tk.END, "   Returns: { \"topic\": \"...\", \"val\": ... }\n\n")
        help_text.insert(tk.END, "2. SETTING STATE:\n")
        help_text.insert(tk.END, "   POST /api/v1/state/PATH/TO/TOPIC\n")
        help_text.insert(tk.END, "   Body: { \"val\": NEW_VALUE }\n\n")
        help_text.insert(tk.END, "3. SYSTEM STATUS:\n")
        help_text.insert(tk.END, "   GET /api/v1/system/status\n\n")
        help_text.insert(tk.END, "4. INTERACTIVE DOCS:\n")
        help_text.insert(tk.END, "   Click 'OPEN API DOCS' to launch Swagger UI.\n")
        help_text.tag_configure("bold", foreground="#ffffff", font=("Courier", 10, "bold"))
        help_text.configure(state="disabled")

        # 4. Footer Info
        self.footer_lbl = tk.Label(self, text="Server URL: -", bg="#2b2b2b", fg="#888888", font=("Helvetica", 8))
        self.footer_lbl.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=2)

    def _start_service(self):
        logger.info("🌐 REST: Starting service...")
        REST_MODULE.start()
        self.after(500, self._refresh_ui)

    def _stop_service(self):
        logger.warning("🌐 REST: Stopping service...")
        REST_MODULE.stop()
        self.after(500, self._refresh_ui)

    def _open_browser(self):
        status = REST_MODULE.get_status()
        if status.get("docs_url"):
            webbrowser.open(status["docs_url"])

    def _refresh_ui(self):
        status = REST_MODULE.get_status()
        
        if status["running"]:
            self.status_lbl.configure(text=f"ACTIVE: {status['host']}:{status['port']}", fg="#00ff00")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.footer_lbl.configure(text=f"Server URL: {status['url']} (Swagger Docs: {status['docs_url']})")
        else:
            self.status_lbl.configure(text="OFFLINE", fg="#ff4444")
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.footer_lbl.configure(text="Server URL: OFFLINE")

        # Update Routes Tree
        for item in self.routes_tree.get_children():
            self.routes_tree.delete(item)
            
        for route in status.get("routes", []):
            self.routes_tree.insert("", "end", text=route["path"], values=(", ".join(route["methods"]),))

    def on_rest_activity(self, method, path, status_code, payload=None):
        """Callback for real-time traffic."""
        self.after(0, lambda: self._add_log_entry(method, path, status_code))

    def _add_log_entry(self, method, path, status_code):
        now = datetime.datetime.now()
        ts = now.strftime("%H:%M:%S.%f")[:-3]
        
        tag = "2xx"
        if 400 <= status_code < 500: tag = "4xx"
        elif status_code >= 500: tag = "5xx"
        
        self.tree.insert("", 0, values=(ts, method, path, status_code), tags=(tag,))
        
        if len(self.tree.get_children()) > 50:
            self.tree.delete(self.tree.get_children()[-1])

    def render(self):
        pass

    def destroy(self):
        try: 
            REST_MODULE.remove_monitor_callback(self.on_rest_activity)
        except Exception:
            pass
        super().destroy()

def get_gui_class():
    return RestDashboard
