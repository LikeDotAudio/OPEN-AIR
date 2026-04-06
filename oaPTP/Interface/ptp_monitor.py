import sys

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# 1588_PTP_Monitor/ptp_monitor.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized PTP (Precision Time Protocol) Monitor GUI.

import tkinter as tk
from tkinter import ttk
import datetime
from pathlib import Path
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from .Core.ptp_processor import PTPDataProcessor
from .Core.ptp_meter_panel import PTPMeterPanel
from .Core.ptp_dissector_engine import PTPDissectorEngine

from oaPTP.Core.ptp import register_ptp_callback, unregister_ptp_callback
from oaConfiguration.FileReaders.config_reader import Config
from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

app_constants = Config.get_instance()

class PtpMonitor(tk.Frame, TransparencyMixin):
    """
    Modular GUI monitor for real-time PTP packet inspection and time analysis.
    """

    def __init__(self, parent, json_path=None, config=None, **kwargs):
        self.config_data = config or {}
        self.theme_colors = self.config_data.get("theme_colors", THEMES[DEFAULT_THEME])
        self._packet_data_cache = {}
        
        if "bg" not in kwargs: kwargs["bg"] = self.theme_colors.get("bg", "#2b2b2b")
        super().__init__(parent, **kwargs)
        
        self._setup_styles()
        self._setup_ui()
        
        # Transparency integration
        builder = self._find_builder(self)
        if builder: self._apply_transparency(self, None, {}, builder)
        
        # Meter Cluster initialization
        self.meter_panel = PTPMeterPanel(self.meter_container, builder) if builder else None
        
        register_ptp_callback(self.on_ptp_packet)
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🖥️ PTP Monitor Initialized.", "DEBUG")

    def _find_builder(self, widget):
        from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder): return curr
            try: curr = curr.master
            except: break
        return None

    def _setup_styles(self):
        self.style = ttk.Style()
        bg = self.theme_colors.get("bg", "#2b2b2b")
        self.style.configure("Dark.TFrame", background=bg)
        self.style.configure("Dark.TLabel", background=bg, foreground=self.theme_colors.get("fg", "#dcdcdc"))
        self.style.configure("Ptp.Treeview", background="#3c3f41", fieldbackground="#3c3f41", foreground="black")

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.v_paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=self.cget("bg"), bd=0, sashwidth=4)
        self.v_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 1. TOP: Packet List
        self.list_container = tk.Frame(self.v_paned, bg=self.cget("bg"))
        self.v_paned.add(self.list_container, stretch="always", height=200)
        ttk.Label(self.list_container, text="PTP (IEEE 1588) Monitor", font=("Arial", 12, "bold"), style="Dark.TLabel").pack(pady=(0,5))
        
        cols = ("Time", "Source IP", "Type", "Domain", "Seq ID", "Clock Identity")
        self.packet_tree = ttk.Treeview(self.list_container, columns=cols, show="headings", style="Ptp.Treeview")
        for c in cols:
            self.packet_tree.heading(c, text=c); self.packet_tree.column(c, width=150 if c=="Time" else (250 if c=="Clock Identity" else 100))
        self.packet_tree.tag_configure("Sync", foreground="#006400"); self.packet_tree.tag_configure("Announce", foreground="#4444ff")
        
        sy = ttk.Scrollbar(self.list_container, orient=tk.VERTICAL, command=self.packet_tree.yview)
        self.packet_tree.configure(yscrollcommand=sy.set); self.packet_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); sy.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.packet_tree.bind("<<TreeviewSelect>>", self.on_packet_select)

        # 2. MIDDLE: Meters
        self.meter_container = tk.Frame(self.v_paned, bg=self.cget("bg"))
        self.v_paned.add(self.meter_container, stretch="never", height=180)

        # 3. BOTTOM: Dissector
        self.dissect_container = tk.Frame(self.v_paned, bg=self.cget("bg"))
        self.v_paned.add(self.dissect_container, stretch="always", height=300)
        ttk.Label(self.dissect_container, text="Packet Dissector", font=("Arial", 10, "bold"), style="Dark.TLabel").pack(anchor="w", pady=(5,0))
        
        self.dissector_tree = ttk.Treeview(self.dissect_container, columns=("Value"), show="tree headings", style="Ptp.Treeview")
        self.dissector_tree.heading("#0", text="Field"); self.dissector_tree.heading("Value", text="Protobuf Content")
        dsy = ttk.Scrollbar(self.dissect_container, orient=tk.VERTICAL, command=self.dissector_tree.yview)
        self.dissector_tree.configure(yscrollcommand=dsy.set); self.dissector_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); dsy.pack(side=tk.RIGHT, fill=tk.Y)

        # 4. Controls
        ctrls = tk.Frame(self, bg=self.cget("bg")); ctrls.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        ttk.Button(ctrls, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        self.btn_copy = ttk.Button(ctrls, text="COPY PTP SNIFFER COMMAND", command=self.copy_sniffer_command)
        self.btn_copy.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def on_ptp_packet(self, data):
        ordered, ts_str, tag = PTPDataProcessor.process_packet(data)
        iid = self.packet_tree.insert("", 0, values=(ts_str, data["source_ip"], data["message_type"], data["domain"], data["sequence_id"], data["clock_identity"]), tags=(tag))
        self._packet_data_cache[iid] = ordered
        
        self.packet_tree.selection_set(iid); self.packet_tree.see(iid); self.on_packet_select()
        if len(self.packet_tree.get_children()) > 100:
            last = self.packet_tree.get_children()[-1]; self.packet_tree.delete(last); self._packet_data_cache.pop(last, None)

    def on_packet_select(self, event=None):
        sel = self.packet_tree.selection()
        if not sel: return
        self.dissector_tree.delete(*self.dissector_tree.get_children())
        data = self._packet_data_cache.get(sel[0])
        if data:
            PTPDissectorEngine.populate(self.dissector_tree, "", data)
            if self.meter_panel: self.meter_panel.update(data.get("timestamp", 0))

    def clear_log(self):
        self.packet_tree.delete(*self.packet_tree.get_children()); self.dissector_tree.delete(*self.dissector_tree.get_children()); self._packet_data_cache = {}

    def copy_sniffer_command(self):
        p = Path(__file__).resolve().parents[5] / "oaPTP" / "PTPtester.py"
        c = f"sudo PYTHONPATH=$(python3 -m site --user-site) python3 {p} --broker {app_constants.MQTT_BROKER_ADDRESS} --port {app_constants.MQTT_BROKER_PORT}"
        self.clipboard_clear(); self.clipboard_append(c)
        ot = self.btn_copy.cget("text"); self.btn_copy.config(text="PASTE copied text into terminal")
        self.after(3000, lambda: self.btn_copy.config(text=ot))

    def render(self):
        bg = self.cget("bg")
        self.style.configure("Ptp.Treeview", background=bg, fieldbackground=bg)
        self.style.configure("Dark.TFrame", background=bg); self.style.configure("Dark.TLabel", background=bg)
        for f in [self.v_paned, self.list_container, self.meter_container, self.dissect_container, ctrls if hasattr(self, 'ctrls') else None]:
            if f: f.config(bg=bg)
        if self.meter_panel: self.meter_panel.stack.config(bg=bg)

    def destroy(self): unregister_ptp_callback(self.on_ptp_packet); super().destroy()