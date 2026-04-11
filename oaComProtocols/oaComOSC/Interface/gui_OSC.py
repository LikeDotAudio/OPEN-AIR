# /home/anthony/Documents/OPEN-AIR/oaComProtocols.oaComOSC/Interface/gui_OSC.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1000.1
#
# Description: Advanced OSC Monitor & Control Hub. 
# This file contains the primary implementation logic for the OSC GUI.

import os
import sys
import pathlib
from pathlib import Path

# --- Path Guard: Ensure project root is in sys.path ---
current_path = Path(__file__).resolve()
root_path = current_path
for parent in current_path.parents:
    if (parent / "oaComBroker").exists() and (parent / "oaGui/Assets").exists():
        root_path = parent
        break

if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
from loguru import logger
from oaLogging.Entry import logger as logger_oa
import inspect
from oaLogging.Methods.matrix_gate import matrix_log
from loguru import logger
import tkinter as tk
from tkinter import ttk
import datetime
from pathlib import Path

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass

# --- Import the OSC Entry point for manager access ---
import oaComProtocols.oaComOSC.Entry as OSC_MODULE

# --- Define the actual GUI class ---
class OscDashboardImplementation(tk.Frame, TransparencyMixin):
    """
    OSC Status, Control & Monitor.
    Manages the OSC Bridge lifecycle and provides deep inspection of traffic.
    This class contains the full implementation.
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
            app_inst = self.config_data.get("app_instance")
            mqtt_conn = self.config_data.get("mqtt_connection_manager") or (getattr(app_inst, "mqtt_connection_manager", None) if app_inst else None)
            
            # This will initialize or update the singleton instance
            OSC_MODULE.get_manager(state_cache_manager=state_cache, mqtt_connection_manager=mqtt_conn)
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🅾️ OscDashboard: OSCManager linked successfully.", "INFO")
        except Exception as e:
            logger.error(f"🅾️ OscDashboard: Standalone setup failed: {e}")

        # Register for activity callbacks via the Entry point
        try:
            OSC_MODULE.add_monitor_callback(self.on_osc_activity)
        except Exception as e:
            logger.error(f"OscDashboard: Failed to register callback: {e}")
            
        self._refresh_ui()
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedules a periodic status check."""
        self._refresh_ui()
        if not getattr(self, '_destroyed', False):
            self.after(2000, self._schedule_refresh)

    def _find_builder_instance(self, widget):
        """
        ⚡ DECOUPLED: Searches the widget tree for a builder instance without 
        direct dependency on oaGuiBuilder classes.
        """
        curr = widget
        while curr:
            # Check for generic 'builder' or 'app_instance'
            if hasattr(curr, 'builder'):
                return getattr(curr, 'builder')
            if hasattr(curr, 'app_instance'):
                return curr
            try: curr = curr.master
            except: break
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

        # 2. Control Bar (Simplified: No Start/Stop/Restart/Toggle as OSC is now always online)
        ctrl_bar = tk.Frame(self, bg="#333333", height=40)
        ctrl_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(ctrl_bar, text="MANDATORY SYSTEM SERVICE: ALWAYS ONLINE", 
                 font=("Helvetica", 9, "bold italic"), fg="#00ff00", bg="#333333").pack(side=tk.LEFT, padx=10, pady=10)

        # 3. Split View (Monitor + Investigation)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Live Monitor ---
        monitor_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(monitor_frame, weight=3)

        cols = ("Time", "Dir", "Address", "Value", "Topic")
        self.tree = ttk.Treeview(monitor_frame, columns=cols, show="headings", style="SMPTE.Treeview")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col!="Value" and col!="Address" else 200)
        
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
        
        # Update Header (Buttons are removed)
        if status["running"]:
            self.status_lbl.configure(text=f"ACTIVE: {status['rx_socket']}", fg="#00ff00")
        else:
            self.status_lbl.configure(text="BOOTING...", fg="#ffff00")

        # Update Detail Tree
        for item in self.info_tree.get_children():
            self.info_tree.delete(item)
            
        self.info_tree.insert("", "end", text="RX Socket", values=(status["rx_socket"],))
        self.info_tree.insert("", "end", text="TX Socket", values=(status["tx_socket"],))
        self.info_tree.insert("", "end", text="Active Routes", values=(status["routes_count"],))
        self.info_tree.insert("", "end", text="Bridge Mode", values=("Always Enabled",))

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
        self.inspect_text.insert(tk.END, "╔════════════ OSC MESSAGE DISSECTION ════════════╗", "header")
        self.inspect_text.insert(tk.END, f"  TIME       : {data['ts']}")
        self.inspect_text.insert(tk.END, f"  DIRECTION  : {data['direction']} ({'Incoming' if data['direction'] == 'RX' else 'Outgoing'})")
        self.inspect_text.insert(tk.END, "╟──────────────────────────────────────────────────╢")
        self.inspect_text.insert(tk.END, f"  OSC ADDR   : {data['address']}")
        self.inspect_text.insert(tk.END, f"  VALUE      : {data['value']}")
        self.inspect_text.insert(tk.END, f"  TYPE       : {type(data['value']).__name__}")
        
        if data['topic']:
            self.inspect_text.insert(tk.END, "╟── ROUTING ───────────────────────────────────────╢")
            self.inspect_text.insert(tk.END, f"  MQTT TOPIC : {data['topic']}")
            
            # Deduce if it's a standard mapping
            is_std = data['topic'].startswith("OPEN-AIR/")
            self.inspect_text.insert(tk.END, f"  MAPPING    : {'Standard Auto-Map' if is_std else 'Manual User Route'}")

        self.inspect_text.insert(tk.END, "╚═════════════════════ END ════════════════════════╝")

    def render(self):
        """Required by TransparencyMixin to sync background colors."""
        pass

    def destroy(self):
        self._destroyed = True
        # Unregister via the Entry point
        try: 
            OSC_MODULE.remove_monitor_callback(self.on_osc_activity)
        except Exception as e:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"OscDashboard: Failed to remove monitor callback: {e}", "TRACE")
        super().destroy()
