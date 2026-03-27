# 55_OSC/gui_OSC.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1000.1
#
# Description: Advanced OSC Monitor & Control Hub. 
# Provides service management, bridge toggling, and live traffic inspection.

import tkinter as tk
from tkinter import ttk
import datetime
import sys
import os
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

import oaComOSC.Entry as OSC_MODULE

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Entry import logger
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

class OscDashboard(tk.Frame, TransparencyMixin):
    """
    OSC Status, Control & Monitor.
    Manages the OSC Bridge lifecycle and provides deep inspection of traffic.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        
        # Activity cache for investigation: { ts_ms_str: msg_dict }
        self._activity_cache = {}
        
        self._setup_ui()
        
        # --- Standalone Initialization ---
        # ⚡ STANDALONE: Ensure the OSC manager is initialized with GUI-provided managers if possible.
        try:
            state_cache = self.config_data.get("state_cache_manager")
            mqtt_conn = self.config_data.get("mqtt_connection_manager") or \
                        (getattr(self.config_data.get("app_instance"), "mqtt_connection_manager", None) if self.config_data.get("app_instance") else None)
            
            # This will initialize or update the singleton instance
            OSC_MODULE.get_manager(state_cache_manager=state_cache, mqtt_connection_manager=mqtt_conn)
            if LOCAL_DEBUG: logger.info("🅾️ OscDashboard: OSCManager linked successfully.")
        except Exception as e:
            logger.error(f"🅾️ OscDashboard: Standalone setup failed: {e}")

        # Register for activity callbacks via the Entry point
        try:
            OSC_MODULE.add_monitor_callback(self.on_osc_activity)
        except Exception as e:
            logger.error(f"OscDashboard: Failed to register callback: {e}")
            
        self._refresh_ui()

    def _find_builder_instance(self, widget):
        """Recursively searches for a DynamicGuiBuilder in the parent hierarchy."""
        try:
            from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
            curr = widget
            while curr:
                if isinstance(curr, DynamicGuiBuilder):
                    return curr
                curr = curr.master
        except Exception:
            pass
        return None

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))
        
        tk.Label(header, text="🅾️ OSC CONTROL HUB", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
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

        self.btn_restart = tk.Button(ctrl_bar, text="♻ RESTART", bg="#333344", fg="#ffffff", font=("Helvetica", 9, "bold"), 
                                    command=self._restart_service, width=10, relief="raised", bd=2)
        self.btn_restart.pack(side=tk.LEFT, padx=5, pady=5)

        # Bridge Mode Toggle
        self.bridge_var = tk.BooleanVar(value=True)
        self.chk_bridge = tk.Checkbutton(ctrl_bar, text="ENABLE BRIDGE MODE", variable=self.bridge_var, 
                                        bg="#333333", fg="#00ff00", activebackground="#333333", activeforeground="#00ff00",
                                        selectcolor="#1a1a1a", font=("Helvetica", 9, "bold"), command=self._toggle_bridge)
        self.chk_bridge.pack(side=tk.RIGHT, padx=20)

        # 3. Split View (Monitor + Investigation)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Live Monitor ---
        monitor_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(monitor_frame, weight=3)

        cols = ("Time", "Dir", "Address", "Value", "Topic")
        self.tree = ttk.Treeview(monitor_frame, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        
        self.tree.column("Time", width=120)
        self.tree.column("Address", width=250, anchor="w")
        self.tree.column("Value", width=150)
        self.tree.column("Topic", width=250, anchor="w")

        # Tags
        self.tree.tag_configure("RX", foreground="#aa00ff")   # Purple
        self.tree.tag_configure("TX", foreground="#ff00ff")   # Magenta
        self.tree.tag_configure("MQTT", foreground="#00ff00") # Green

        vsb = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_packet)

        # --- BOTTOM: Investigation Pane ---
        inspect_frame = tk.Frame(self.paned, bg="#000000", bd=1, relief="sunken")
        self.paned.add(inspect_frame, weight=2)

        inspect_header = tk.Frame(inspect_frame, bg="#1a1a1a")
        inspect_header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(inspect_header, text="🔍 OSC MESSAGE DISSECTOR", font=("Helvetica", 10, "bold"), fg="#888888", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)
        
        tk.Button(inspect_header, text="CLEAR LOG", bg="#333333", fg="#ffffff", font=("Helvetica", 7), 
                  command=self._clear_monitor, bd=1).pack(side=tk.RIGHT, padx=5, pady=2)

        self.inspect_text = tk.Text(inspect_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), bd=0, highlightthickness=0)
        self.inspect_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.inspect_text.tag_configure("header", foreground="#ffffff", font=("Courier", 10, "bold"))

        # 4. Bottom Port Status
        status_frame = tk.LabelFrame(self, text="Network & Routing Status", bg="#2b2b2b", fg="#888888")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False, padx=15, pady=(5, 10))

        self.info_tree = ttk.Treeview(status_frame, columns=("Value"), show="tree", height=4)
        self.info_tree.heading("#0", text="Property")
        self.info_tree.column("#0", width=200)
        self.info_tree.pack(fill=tk.X, expand=True, padx=5, pady=5)

    def _start_service(self):
        logger.info("📡 OSC: Starting service...")
        OSC_MODULE.start()
        self._refresh_ui()

    def _stop_service(self):
        logger.warning("📡 OSC: Stopping service...")
        OSC_MODULE.stop()
        self._refresh_ui()

    def _restart_service(self):
        logger.info("📡 OSC: Restarting service...")
        OSC_MODULE.stop()
        self.after(500, OSC_MODULE.start)
        self.after(600, self._refresh_ui)

    def _toggle_bridge(self):
        enabled = self.bridge_var.get()
        logger.info(f"📡 OSC: Setting bridge mode to {enabled}")
        OSC_MODULE.set_bridge_mode(enabled)
        self._refresh_ui()

    def _clear_monitor(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._activity_cache.clear()
        self.inspect_text.delete("1.0", tk.END)

    def _refresh_ui(self):
        """Pulls status from the OSC module's Entry point."""
        try:
            status = OSC_MODULE.status()
        except Exception as e:
            logger.error(f"OscDashboard: Failed to get status: {e}")
            return
        
        # Update Header & Buttons
        if status["running"]:
            self.status_lbl.configure(text=f"ACTIVE: {status['rx_socket']}", fg="#00ff00")
            self.btn_start.configure(state="disabled", bg="#1a2a1a")
            self.btn_stop.configure(state="normal", bg="#4a1a1a")
        else:
            self.status_lbl.configure(text="OFFLINE", fg="#ff4444")
            self.btn_start.configure(state="normal", bg="#1a4a1a")
            self.btn_stop.configure(state="disabled", bg="#2a1a1a")

        self.bridge_var.set(status["bridge_mode"])

        # Update Detail Tree
        for item in self.info_tree.get_children():
            self.info_tree.delete(item)
            
        self.info_tree.insert("", "end", text="RX Socket", values=(status["rx_socket"],))
        self.info_tree.insert("", "end", text="TX Socket", values=(status["tx_socket"],))
        self.info_tree.insert("", "end", text="Active Routes", values=(status["routes_count"],))
        self.info_tree.insert("", "end", text="Bridge Mode", values=("Enabled" if status["bridge_mode"] else "Observer Only",))

    def on_osc_activity(self, direction, address, value, topic=None):
        """Callback from the OSC module."""
        if direction == "STATUS_UPDATE":
            self.after(0, self._refresh_ui)
        else:
            self.after(0, lambda: self._add_log_entry(direction, address, value, topic))

    def _add_log_entry(self, direction, address, value, topic):
        now = datetime.datetime.now()
        ts = now.strftime("%H:%M:%S.%f")[:-3]
        
        # ⚡ STACK BEHAVIOR: Insert at TOP
        item_id = self.tree.insert("", 0, values=(ts, direction, address, value, topic or "-"), tags=(direction,))
        
        # Cache for investigation
        self._activity_cache[ts] = {
            "ts": ts,
            "direction": direction,
            "address": address,
            "value": value,
            "topic": topic
        }

        if len(self.tree.get_children()) > 100:
            last_item = self.tree.get_children()[-1]
            last_ts = self.tree.item(last_item)["values"][0]
            if last_ts in self._activity_cache: del self._activity_cache[last_ts]
            self.tree.delete(last_item)

    def on_select_packet(self, event):
        """Populates the investigation pane with detailed OSC metadata."""
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        ts = item["values"][0]
        data = self._activity_cache.get(ts)
        
        if not data: return
        
        self.inspect_text.delete("1.0", tk.END)
        self.inspect_text.insert(tk.END, "╔════════════ OSC MESSAGE DISSECTION ════════════╗\n", "header")
        self.inspect_text.insert(tk.END, f"  TIME       : {data['ts']}\n")
        self.inspect_text.insert(tk.END, f"  DIRECTION  : {data['direction']} ({'Incoming' if data['direction'] == 'RX' else 'Outgoing'})\n")
        self.inspect_text.insert(tk.END, "╟──────────────────────────────────────────────────╢\n")
        self.inspect_text.insert(tk.END, f"  OSC ADDR   : {data['address']}\n")
        self.inspect_text.insert(tk.END, f"  VALUE      : {data['value']}\n")
        self.inspect_text.insert(tk.END, f"  TYPE       : {type(data['value']).__name__}\n")
        
        if data['topic']:
            self.inspect_text.insert(tk.END, "╟── ROUTING ───────────────────────────────────────╢\n")
            self.inspect_text.insert(tk.END, f"  MQTT TOPIC : {data['topic']}\n")
            
            # Deduce if it's a standard mapping
            is_std = data['topic'].startswith("OPEN-AIR/")
            self.inspect_text.insert(tk.END, f"  MAPPING    : {'Standard Auto-Map' if is_std else 'Manual User Route'}\n")

        self.inspect_text.insert(tk.END, "╚═════════════════════ END ════════════════════════╝\n")

    def render(self):
        """Required by TransparencyMixin to sync background colors."""
        pass

    def destroy(self):
        # Unregister via the Entry point
        try: 
            OSC_MODULE.remove_monitor_callback(self.on_osc_activity)
        except Exception as e:
            logger.trace(f"OscDashboard: Failed to remove monitor callback: {e}")
        super().destroy()

def get_gui_class():
    return OscDashboard
