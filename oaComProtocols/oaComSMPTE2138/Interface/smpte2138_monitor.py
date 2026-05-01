# /home/anthony/Documents/OPEN-AIR/oaComProtocols.oaComSMPTE2138/Interface/smpte2138_monitor.py
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version: 20260405.2115.1
#
# Description: Elite GUI monitor for the SMPTE ST 2138 protocol.
# This file contains the primary implementation logic.

import datetime
import inspect
import tkinter as tk
from tkinter import ttk

import orjson

from oaComProtocols.oaComMQTT.Core import mqtt_publisher_service

# --- ST 2138 Logic Bridge ---
# --- Standard OPEN-AIR GUI Imports ---
from oaLogging.Methods.matrix_gate import matrix_log
from oaStyle.Core.style import DEFAULT_THEME, THEMES

# --- GUI FALLBACKS (V3.2.1 Decoupling) ---
try:
    from oaGui.Workers.transparency.transparency_mixin import TransparencyMixin
except ImportError:
    class TransparencyMixin:
        """Fallback mixin for standalone execution without GUI manager."""
        def render(self): pass
        def _apply_transparency(self, *args, **kwargs): pass

LOCAL_DEBUG = False

class SMPTE2138MonitorImplementation(tk.Frame, TransparencyMixin):
    """
    ST 2138 Monitor GUI with remote bridge lifecycle control.
    This class provides the full implementation.
    """

    def __init__(self, parent, json_path=None, config=None, **kwargs):
        self.config_data = config if config else {}
        self.theme_colors = self.config_data.get("theme_colors", THEMES[DEFAULT_THEME])
        self._packet_cache = {}

        if "bg" not in kwargs:
            kwargs["bg"] = self.theme_colors.get("bg", "#2b2b2b")

        super().__init__(parent, **kwargs)

        self._setup_styles()
        self._setup_ui()

        builder = self._find_builder(self)
        if builder:
            self._apply_transparency(self, None, {}, builder)

        try:
            # from oaComBroker.Core.event_bus import event_bus
            # event_bus.subscribe("SMPTE2138_TRAFFIC", self._on_bus_update)
            pass
        except ImportError: pass

        self._update_status_loop()

        if LOCAL_DEBUG:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🖥️ [UI] Elite ST 2138 Monitor Online.", "DEBUG")

    def _find_builder(self, widget):
        """
        ⚡ DECOUPLED: Searches the widget tree for a builder instance without 
        direct dependency on oaGui classes.
        """
        curr = widget
        while curr:
            # Check for generic 'builder' or 'app_instance'
            if hasattr(curr, 'builder'):
                return curr.builder
            if hasattr(curr, 'app_instance'):
                return curr
            try: curr = curr.master
            except: break
        return None

    def _setup_styles(self):
        self.style = ttk.Style()
        bg = self.theme_colors.get("bg", "#2b2b2b")
        fg = self.theme_colors.get("fg", "#dcdcdc")

        self.style.configure("SMPTE.TFrame", background=bg)
        self.style.configure("SMPTE.TLabel", background=bg, foreground=fg)
        self.style.configure("SMPTE.Header.TLabel", background=bg,
                             foreground="#00ff00", font=("Arial", 12, "bold"))
        self.style.configure("SMPTE.Stat.TLabel", background=bg,
                             foreground="#aaa", font=("Monospace", 9))
        self.style.configure("SMPTE.Treeview", background="#1e1e1e",
                             fieldbackground="#1e1e1e", foreground="#00ff00")

        self.style.configure("SMPTE.Start.TButton", foreground="white", background="#28a745")
        self.style.configure("SMPTE.Stop.TButton", foreground="white", background="#dc3545")

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)

        # --- TOP: Elite Status Header ---
        self.header_panel = tk.Frame(self, bg="#1a1a1a", height=70, bd=1, relief=tk.RAISED)
        self.header_panel.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # 1. Info & Control
        ctrl_frame = tk.Frame(self.header_panel, bg="#1a1a1a")
        ctrl_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(ctrl_frame, text="ST 2138 ENGINE",
                  style="SMPTE.Header.TLabel").pack(anchor="w")

        btn_frame = tk.Frame(ctrl_frame, bg="#1a1a1a")
        btn_frame.pack(anchor="w", pady=2)

        self.start_btn = ttk.Button(btn_frame, text="START", width=8,
                                    command=lambda: self._send_bridge_cmd(True))
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(btn_frame, text="STOP", width=8,
                                   command=lambda: self._send_bridge_cmd(False))
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # 2. Telemetry Meters
        stats_frame = tk.Frame(self.header_panel, bg="#1a1a1a")
        stats_frame.pack(side=tk.LEFT, expand=True)

        self.status_var = tk.StringVar(value="STATUS: UNKNOWN")
        self.message_total_var = tk.StringVar(value="MSGS: 0")
        self.rate_var = tk.StringVar(value="RATE: 0.0 message/s")

        ttk.Label(stats_frame, textvariable=self.status_var,
                  style="SMPTE.Stat.TLabel").grid(row=0, column=0, padx=10)
        ttk.Label(stats_frame, textvariable=self.message_total_var,
                  style="SMPTE.Stat.TLabel").grid(row=0, column=1, padx=10)
        ttk.Label(stats_frame, textvariable=self.rate_var,
                  style="SMPTE.Stat.TLabel").grid(row=0, column=2, padx=10)

        # 3. Connection Info
        conn_frame = tk.Frame(self.header_panel, bg="#1a1a1a")
        conn_frame.pack(side=tk.RIGHT, padx=10)

        self.broker_var = tk.StringVar(value="NODE: -")
        ttk.Label(conn_frame, textvariable=self.broker_var,
                  style="SMPTE.Stat.TLabel").pack(anchor="e")

        self.led_canvas = tk.Canvas(conn_frame, width=15, height=15,
                                    bg="#1a1a1a", highlightthickness=0)
        self.led_canvas.pack(side=tk.RIGHT, pady=2)
        self.status_led = self.led_canvas.create_oval(2, 2, 13, 13, fill="grey")

        # --- Main Splitter Area ---
        self.paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=self.cget("bg"),
                                    bd=0, sashwidth=4)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 1. TOP: Log
        self.log_container = tk.Frame(self.paned, bg=self.cget("bg"))
        self.paned.add(self.log_container, stretch="always", height=250)

        cols = ("Time", "Type", "Slot", "OID", "Value")
        self.log_tree = ttk.Treeview(self.log_container, columns=cols,
                                     show="headings", style="SMPTE.Treeview")

        for c in cols:
            self.log_tree.heading(c, text=c, command=lambda _c=c: self._sort_column(_c, False))
            self.log_tree.column(c, width=100 if c!="Value" else 200)

        sy = ttk.Scrollbar(self.log_container, orient=tk.VERTICAL,
                           command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=sy.set)
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sy.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_tree.bind("<<TreeviewSelect>>", self.on_select)

        # 2. BOTTOM: Dissector
        self.dissect_container = tk.Frame(self.paned, bg=self.cget("bg"))
        self.paned.add(self.dissect_container, stretch="always", height=200)

        self.dissector = ttk.Treeview(self.dissect_container, columns=("Value"),
                                      show="tree headings", style="SMPTE.Treeview")
        self.dissector.heading("#0", text="Field")
        self.dissector.heading("Value", text="Protobuf Content")
        self.dissector.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        dsy = ttk.Scrollbar(self.dissect_container, orient=tk.VERTICAL,
                            command=self.dissector.yview)
        self.dissector.configure(yscrollcommand=dsy.set)
        dsy.pack(side=tk.RIGHT, fill=tk.Y)

    def _sort_column(self, col, reverse):
        """Sorts the treeview by the given column."""
        l = [(self.log_tree.set(k, col), k) for k in self.log_tree.get_children('')]

        # Try numeric sort if applicable
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        # Rearrange items in sorted order
        for index, (value, k) in enumerate(l):
            self.log_tree.move(k, '', index)

        # Reverse sort next time
        self.log_tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _send_bridge_cmd(self, active: bool):
        """Dispatches a remote control message to the bridge."""
        topic = "OPEN-AIR/System/Control/SMPTE2138/Bridge"
        payload = {"active": active}
        mqtt_publisher_service.publish_payload(topic, orjson.dumps(payload).decode())
        if LOCAL_DEBUG:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📡 [UI] Sent remote command: BRIDGE={'START' if active else 'STOP'}", "INFO")

    def _update_status_loop(self):
        """Periodic UI task to update status indicators."""
        self.after(1000, self._update_status_loop)

    def _on_bus_update(self, topic, data):
        """Standard event bus handler."""
        self.on_smpte2138_traffic(topic, data)

    def on_smpte2138_traffic(self, topic, data):
        """Callback for new decoded packets and telemetry."""
        self.after(0, lambda: self._update_gui(topic, data))

    def _update_gui(self, topic, data):
        stats = data.get("_stats", {})

        # Update Header
        self.status_var.set(f"ENGINE: {stats.get('status', 'N/A')}")
        self.message_total_var.set(f"TOTAL MSGS: {stats.get('message_count', 0)}")
        self.rate_var.set(f"RATE: {stats.get('rate', 0.0)} message/s")
        self.broker_var.set(f"NODE: {stats.get('broker', '-')}")

        # Update LED
        color = "#00ff00" if stats.get("connected") else "red"
        self.led_canvas.itemconfig(self.status_led, fill=color)

        # Update Log
        message_type = data.get("_message_type", "N/A")
        if message_type in ["HEARTBEAT", "STATUS"]:
            return

        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        iid = self.log_tree.insert("", 0, values=(
            timestamp,
            message_type,
            data.get("slot", "-"),
            data.get("oid", "-"),
            data.get("value", "-")
        ))

        self._packet_cache[iid] = data

        if len(self.log_tree.get_children()) > 200:
            last = self.log_tree.get_children()[-1]
            self.log_tree.delete(last)
            self._packet_cache.pop(last, None)

    def on_select(self, event=None):
        sel = self.log_tree.selection()
        if not sel: return

        self.dissector.delete(*self.dissector.get_children())
        packet = self._packet_cache.get(sel[0])
        if packet:
            self._populate_dissector("", packet)

    def _populate_dissector(self, parent, data):
        for k, v in data.items():
            if k.startswith("_"): continue
            if isinstance(v, dict):
                node = self.dissector.insert(parent, "end", text=k, open=True)
                self._populate_dissector(node, v)
            else:
                self.dissector.insert(parent, "end", text=k, values=(v,))

    def render(self):
        bg = self.cget("bg")
        self.header_panel.config(bg="#1a1a1a")
        self.style.configure("SMPTE.Treeview", background="#1e1e1e")
        self.style.configure("SMPTE.TFrame", background=bg)
        self.style.configure("SMPTE.TLabel", background=bg)

    def destroy(self):
        # from oaComBroker.Core.event_bus import event_bus
        # event_bus.unsubscribe("SMPTE2138_TRAFFIC", self._on_bus_update)
        super().destroy()

def get_gui_class():
    """
    Returns the main GUI class for this module.
    This function is used by GUI discovery mechanisms.
    """
    return SMPTE2138MonitorImplementation

__all__ = ["SMPTE2138MonitorImplementation"]
