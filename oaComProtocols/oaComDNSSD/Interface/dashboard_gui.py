# Interface/dashboard_gui.py
# Author: Gemini (Collaborator)
# Version: 20260414.1030.1

import tkinter as tk
from tkinter import ttk
import json
import webbrowser
from datetime import datetime

class ProtocolDashboard(tk.Frame):
    def __init__(self, parent, config, json_path=None, protocol_name="DNSSD", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.protocol_name = protocol_name
        self.configure(bg="#2b2b2b")
        
        # Styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#1e1e1e", foreground="#d4d4d4", fieldbackground="#1e1e1e", borderwidth=0)
        style.map('Treeview', background=[('selected', '#0078d7')])
        style.configure("Treeview.Heading", background="#3c3c3c", foreground="white", relief="flat")
        
        # Button Frame (Packed FIRST so it stays at the bottom)
        self.btn_frame = tk.Frame(self, bg="#2b2b2b")
        self.btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.clear_btn = tk.Button(self.btn_frame, text="Clear Logs", command=self.clear_logs, bg="#4b6eaf", fg="white", relief="flat")
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        self.open_btn = tk.Button(self.btn_frame, text="Open Target IP", command=self.open_target, bg="#2e7d32", fg="white", relief="flat")
        self.open_btn.pack(side=tk.RIGHT, padx=5)

        # Layout (Packed SECOND so it takes remaining space)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top: Received Announcements
        self.rx_frame = tk.LabelFrame(self.paned, text=f"📥 Received {protocol_name} Announcements", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        self.paned.add(self.rx_frame, weight=1)
        
        self.rx_tree = ttk.Treeview(self.rx_frame, columns=("Time", "Source", "Summary", "IP Address"), show="headings")
        self.rx_tree.heading("Time", text="Time")
        self.rx_tree.heading("Source", text="Source") # Device Name
        self.rx_tree.heading("Summary", text="Service Type") # Service Type
        self.rx_tree.heading("IP Address", text="IP Address")
        self.rx_tree.column("Time", width=120, stretch=False)
        self.rx_tree.column("Source", width=250, stretch=False)
        self.rx_tree.column("Summary", width=300, stretch=False)
        self.rx_tree.column("IP Address", width=150, stretch=False)
        self.rx_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.rx_tree.bind("<<TreeviewSelect>>", self.on_rx_select)
        
        rx_scroll = ttk.Scrollbar(self.rx_frame, orient="vertical", command=self.rx_tree.yview)
        rx_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.rx_tree.configure(yscrollcommand=rx_scroll.set)
        
        # Middle: Transmitted MQTT
        self.tx_frame = tk.LabelFrame(self.paned, text="📤 Transmitted MQTT Messages", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        self.paned.add(self.tx_frame, weight=1)
        
        self.tx_tree = ttk.Treeview(self.tx_frame, columns=("Time", "Topic", "Summary"), show="headings")
        self.tx_tree.heading("Time", text="Time")
        self.tx_tree.heading("Topic", text="Topic")
        self.tx_tree.heading("Summary", text="Summary")
        self.tx_tree.column("Time", width=120, stretch=False)
        self.tx_tree.column("Topic", width=350, stretch=False)
        self.tx_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tx_tree.bind("<<TreeviewSelect>>", self.on_tx_select)
        
        tx_scroll = ttk.Scrollbar(self.tx_frame, orient="vertical", command=self.tx_tree.yview)
        tx_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tx_tree.configure(yscrollcommand=tx_scroll.set)
        
        # Bottom: Packet Analyzer
        self.analyzer_frame = tk.LabelFrame(self.paned, text="🔍 Packet Analyzer", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        self.paned.add(self.analyzer_frame, weight=1)
        
        self.analyzer_text = tk.Text(self.analyzer_frame, bg="#1e1e1e", fg="#4EC9B0", font=("Consolas", 11), insertbackground="white")
        self.analyzer_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        analyzer_scroll = ttk.Scrollbar(self.analyzer_frame, orient="vertical", command=self.analyzer_text.yview)
        analyzer_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.analyzer_text.configure(yscrollcommand=analyzer_scroll.set)
        
        self.rx_data = {}
        self.tx_data = {}
        
    def open_target(self):
        selection = self.rx_tree.selection()
        if not selection:
            return
        details = self.rx_data.get(selection[0], {})
        if not isinstance(details, dict):
            return
            
        ip = None
        port = None
        
        if "source_ip" in details and details["source_ip"] != "Unknown":
            ip = details["source_ip"]
        elif "addresses" in details and details["addresses"]:
            ip = details["addresses"][0]
            
        if "port" in details and details["port"]:
            port = details["port"]
            
        if ip:
            url = f"http://{ip}"
            if port:
                url += f":{port}"
            print(f"🌍 Opening: {url}")
            webbrowser.open(url)

    def clear_logs(self):
        for item in self.rx_tree.get_children():
            self.rx_tree.delete(item)
        for item in self.tx_tree.get_children():
            self.tx_tree.delete(item)
        self.rx_data.clear()
        self.tx_data.clear()
        self.analyzer_text.delete(1.0, tk.END)
        
    def log_rx(self, source, summary, details):
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        # Source is device name, summary is service type (e.g., _ravenna._tcp.local.)
        ip_address = details.get("source_ip", "N/A") if isinstance(details, dict) else "N/A"
        item_id = self.rx_tree.insert("", 0, values=(now, source, summary, ip_address))
        self.rx_data[item_id] = details
        if len(self.rx_tree.get_children()) > 200:
            oldest = self.rx_tree.get_children()[-1]
            self.rx_tree.delete(oldest)
            self.rx_data.pop(oldest, None)
            
    def log_tx(self, topic, summary, details):
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        item_id = self.tx_tree.insert("", 0, values=(now, topic, summary))
        self.tx_data[item_id] = details
        if len(self.tx_tree.get_children()) > 200:
            oldest = self.tx_tree.get_children()[-1]
            self.tx_tree.delete(oldest)
            self.tx_data.pop(oldest, None)

    def on_rx_select(self, event):
        selection = self.rx_tree.selection()
        if selection:
            self.display_details(self.rx_data.get(selection[0], "No details available."))

    def on_tx_select(self, event):
        selection = self.tx_tree.selection()
        if selection:
            self.display_details(self.tx_data.get(selection[0], "No details available."))

    def display_details(self, details):
        self.analyzer_text.delete(1.0, tk.END)
        if isinstance(details, dict):
            formatted = json.dumps(details, indent=4)
            self.analyzer_text.insert(tk.END, formatted)
        else:
            self.analyzer_text.insert(tk.END, str(details))