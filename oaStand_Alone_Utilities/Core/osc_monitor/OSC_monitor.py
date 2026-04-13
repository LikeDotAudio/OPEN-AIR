# OSC_monitor/OSC_monitor.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: !/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

try:
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import BlockingOSCUDPServer
except ImportError:
    print("Error: python-osc is required. Run: pip install python-osc")
    exit(1)

class StandaloneOscMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Standalone OSC Tree Monitor")
        self.root.geometry("900x750")
        
        # Defaulting to 9000 (OPEN-AIR transmits to 9000 by default)
        self.listen_port = tk.IntVar(value=9000) 
        self.server = None
        self.server_thread = None
        self._running = False
        
        # Data storage: address -> last_val, last_ts, tree_id
        self.nodes = {} 
        self.change_history = [] # List of node_paths in order of most recent change
        
        self._setup_ui()
        self._start_server()

    def _setup_ui(self):
        self.root.configure(bg="#1e1e1e")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#2b2b2b", foreground="#dcdcdc", fieldbackground="#2b2b2b", borderwidth=0)
        style.map("Treeview", background=[('selected', '#4a4a4a')])
        style.configure("Treeview.Heading", background="#333333", foreground="#ffffff", borderwidth=1)

        # 1. Header
        header = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=10)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🅾️ OSC MONITOR", font=("Helvetica", 14, "bold"), fg="#00ffff", bg="#1e1e1e").pack(side=tk.LEFT)
        
        controls = tk.Frame(header, bg="#1e1e1e")
        controls.pack(side=tk.RIGHT)
        
        tk.Label(controls, text="Port:", fg="#ffffff", bg="#1e1e1e").pack(side=tk.LEFT, padx=5)
        self.port_entry = ttk.Entry(controls, textvariable=self.listen_port, width=6)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        self.toggle_btn = tk.Button(controls, text="Stop Server", bg="#ff4444", fg="#ffffff", command=self._toggle_server)
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Status: Starting...")
        self.status_label = tk.Label(header, textvariable=self.status_var, font=("Courier", 10), fg="#00ff00", bg="#1e1e1e")
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # 2. Main Content (Paned Window for Log + Tree)
        self.paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Recent Activity Log ---
        log_frame = tk.LabelFrame(self.paned, text="Recent Events (Live Feed)", bg="#1e1e1e", fg="#888888")
        self.paned.add(log_frame, weight=1)
        
        cols = ("Time", "Address", "Value")
        self.log_tree = ttk.Treeview(log_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.log_tree.heading(col, text=col)
            self.log_tree.column(col, width=150, anchor="center")
        self.log_tree.column("Address", width=400, anchor="w")
        
        lsb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=lsb.set)
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lsb.pack(side=tk.RIGHT, fill=tk.Y)

        # --- BOTTOM: Hierarchy Tree View ---
        tree_frame = tk.LabelFrame(self.paned, text="Address Hierarchy (Latest Values)", bg="#1e1e1e", fg="#888888")
        self.paned.add(tree_frame, weight=2)
        
        self.tree = ttk.Treeview(tree_frame, columns=("Value", "Last Update"), show="tree headings")
        self.tree.heading("#0", text="OSC Address Path")
        self.tree.heading("Value", text="Current Value")
        self.tree.heading("Last Update", text="Last Update")
        
        self.tree.column("#0", width=400)
        self.tree.column("Value", width=150, anchor="center")
        self.tree.column("Last Update", width=150, anchor="center")
        
        # Tree Tags for Fading
        self.tree.tag_configure("fade_0", foreground="#00ff00") # Green (Latest)
        self.tree.tag_configure("fade_1", foreground="#ffff00") # Yellow (1 command ago)
        self.tree.tag_configure("fade_2", foreground="#ff0000") # Red (2 commands ago)
        self.tree.tag_configure("fade_3", foreground="#ff8888") # Pinkish Red (3 commands ago)
        self.tree.tag_configure("fade_4", foreground="#dcdcdc") # White (4+ commands ago)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # 3. Footer / Controls
        footer = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=5)
        footer.pack(fill=tk.X)
        
        tk.Button(footer, text="Clear Everything", command=self._clear_all, bg="#444444", fg="#ffffff").pack(side=tk.LEFT)
        tk.Label(footer, text="Independent Process (No OPEN-AIR Dependencies)", font=("Helvetica", 8), fg="#666666", bg="#1e1e1e").pack(side=tk.RIGHT)

    def _toggle_server(self):
        if self._running:
            self._stop_server()
        else:
            self._start_server()

    def _start_server(self):
        if self._running: return
        
        port = self.listen_port.get()
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._on_osc_message)
        
        try:
            self.server = BlockingOSCUDPServer(("0.0.0.0", port), dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self._running = True
            
            self.status_var.set(f"Listening on port: {port}")
            self.status_label.config(fg="#00ff00")
            self.toggle_btn.config(text="Stop Server", bg="#ff4444")
            self.port_entry.config(state="disabled")
        except Exception as e:
            self.status_var.set(f"Port {port} in use / Error")
            self.status_label.config(fg="#ff4444")
            messagebox.showerror("Server Error", f"Could not start server on port {port}:\n\n{e}")
            self._running = False
            self.toggle_btn.config(text="Start Server", bg="#00aa00")
            self.port_entry.config(state="normal")

    def _stop_server(self):
        if not self._running: return
        
        self._running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        
        self.status_var.set("Server Stopped")
        self.status_label.config(fg="#888888")
        self.toggle_btn.config(text="Start Server", bg="#00aa00")
        self.port_entry.config(state="normal")

    def _on_osc_message(self, address, *args):
        if not self._running: return
        
        # Flatten value
        if len(args) == 1:
            value = args[0]
            if isinstance(value, float): value = round(value, 4)
        else:
            value = str(args)
            
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Schedule UI update on main thread
        self.root.after(0, lambda: self._sync_ui(address, value, timestamp))

    def _sync_ui(self, address, value, timestamp):
        # 1. Update Recent Activity Log (Top)
        self.log_tree.insert("", 0, values=(timestamp, address, value))
        # Keep only last 50 events
        if len(self.log_tree.get_children()) > 50:
            self.log_tree.delete(self.log_tree.get_children()[-1])

        # 2. Update Hierarchy Tree (Bottom)
        parts = [p for p in address.split("/") if p]
        parent = ""
        full_node_path = address
        
        for i, part in enumerate(parts):
            node_path = "/" + "/".join(parts[:i+1])
            
            if node_path not in self.nodes:
                is_leaf = (i == len(parts) - 1)
                display_val = value if is_leaf else ""
                display_ts = timestamp if is_leaf else ""
                
                node_id = self.tree.insert(parent, "end", text=part, values=(display_val, display_ts), open=True)
                self.nodes[node_path] = node_id
            else:
                if i == len(parts) - 1:
                    node_id = self.nodes[node_path]
                    self.tree.item(node_id, values=(value, timestamp))
            
            parent = self.nodes[node_path]

        # 3. Visual Fading Logic
        # Update change history
        if full_node_path in self.change_history:
            self.change_history.remove(full_node_path)
        self.change_history.insert(0, full_node_path)
        if len(self.change_history) > 10:
            self.change_history.pop()

        # Re-apply tags to all nodes in history
        for i, path in enumerate(self.change_history):
            if path in self.nodes:
                node_id = self.nodes[path]
                tag = f"fade_{min(i, 4)}"
                self.tree.item(node_id, tags=(tag,))

    def _clear_all(self):
        # Clear Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.nodes.clear()
        self.change_history.clear()
        # Clear Log
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

    def shutdown(self):
        self._stop_server()

if __name__ == "__main__":
    root = tk.Tk()
    app = StandaloneOscMonitor(root)
    
    def on_close():
        app.shutdown()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
