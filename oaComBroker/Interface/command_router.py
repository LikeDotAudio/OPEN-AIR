import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# 3_Command_Router/command_router.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
import time

# --- Standard Debug Logging Setup ---
from loguru import logger
from oaConfigurationManager.FileReaders.config_reader import Config
from oaComBroker.Core.protocol_router.manager import ProtocolRouter
from .protocol_matrix import ProtocolMatrix

app_constants = Config.get_instance()

class CommandRouter(tk.Frame):
    """
    Centralized Hub-and-Spoke Command Monitor.
    Displays all traffic with Deep Packet Inspection.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        self.router = ProtocolRouter.get_instance()
        
        # Selection state for Splinking
        self.src_var = tk.StringVar(value="")
        self.dest_var = tk.StringVar(value="")
        self._src_utp = None
        self._dest_utp = None
        
        self._setup_ui()
        
        # Register as observer of the central protocol router
        self.router.register_cache_observer(self.on_router_event)

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        
        tk.Label(header, text="🌐 COMMAND ROUTER & INVESTIGATION", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        self.status_var = tk.StringVar(value=f"Instance Identity: {self.router.GUID}")
        tk.Label(header, textvariable=self.status_var, font=("Courier", 10, "bold"), fg="#00ff00", bg="#2b2b2b").pack(side=tk.RIGHT, padx=20)

        # ⚡ PROTOCOL ENABLEMENT MATRIX
        self._setup_protocol_matrix()

        # 2. Split View (Monitor + Investigation)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Firehose Monitor ---
        monitor_container = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(monitor_container, weight=3)

        self.tree_frame = tk.Frame(monitor_container, bg="#2b2b2b")
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Machine Time", "Source", "GUID", "Strategy", "Topic", "Value")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show="headings", height=15)
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.column("Topic", width=300, anchor="w")
        self.tree.column("Machine Time", width=150)
        self.tree.column("GUID", width=80)
        self.tree.column("Strategy", width=150)

        # Tags
        self.tree.tag_configure("HERE", foreground="#00ff00") # Bright Green
        self.tree.tag_configure("REMOTE", background="#440000", foreground="yellow") # High-Contrast Remote Alert
        self.tree.tag_configure("MIDI", foreground="#ff00ff")   # Magenta
        self.tree.tag_configure("OSC", foreground="#00ffff")    # Neon Blue/Cyan
        self.tree.tag_configure("MUTATION", background="#440000", foreground="red") # Mutation alert
        self.tree.tag_configure("SYSTEM", foreground="#888888") # Grey
        self.tree.tag_configure("SPLINK", background="#1a1a1a", foreground="#a0a0a0") # Subtle Dark Grey Highlight

        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_packet)

        # --- SPLINK CONTROL BAR (Below Tree) ---
        splink_bar = tk.Frame(monitor_container, bg="#1a1a1a", pady=5)
        splink_bar.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(splink_bar, text="SPLINK:", font=("Helvetica", 10, "bold"), fg="#888888", bg="#1a1a1a").pack(side=tk.LEFT, padx=10)
        
        self.src_entry = tk.Entry(splink_bar, textvariable=self.src_var, bg="#000000", fg="#00ff00", insertbackground="white", width=40, bd=1, relief="flat")
        self.src_entry.pack(side=tk.LEFT, padx=5)

        self.splink_btn = tk.Button(
            splink_bar, 
            text="🔗 SPLINK", 
            command=self.create_direct_splink,
            bg="#2b2b2b",
            fg="#888888",
            font=("Helvetica", 10, "bold"),
            padx=10,
            bd=1,
            relief="raised"
        )
        self.splink_btn.pack(side=tk.LEFT, padx=10)

        self.dest_entry = tk.Entry(splink_bar, textvariable=self.dest_var, bg="#000000", fg="#ffff00", insertbackground="white", width=40, bd=1, relief="flat")
        self.dest_entry.pack(side=tk.LEFT, padx=5)

        # --- BOTTOM: Investigation Pane ---
        inspect_container = tk.Frame(self.paned, bg="#000000", bd=1, relief="sunken")
        self.paned.add(inspect_container, weight=2)

        tk.Label(inspect_container, text="🔍 DUAL PACKET INVESTIGATION & SPLINK DISCOVERY", font=("Helvetica", 10, "bold"), fg="#888888", bg="#000000").pack(side=tk.TOP, anchor="nw", padx=5)
        
        # Dual Column Layout
        self.inspect_split = tk.Frame(inspect_container, bg="#000000")
        self.inspect_split.pack(fill=tk.BOTH, expand=True)

        # Column 1 (Source Candidate)
        col1 = tk.Frame(self.inspect_split, bg="#000000")
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(col1, text="[ SOURCE ]", font=("Helvetica", 8, "bold"), fg="#00ff00", bg="#000000").pack(anchor="nw", padx=10)
        self.inspect_text_src = tk.Text(col1, bg="#000000", fg="#00ff00", font=("Courier", 9), bd=0, highlightthickness=0)
        self.inspect_text_src.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Column 2 (Dest Candidate)
        col2 = tk.Frame(self.inspect_split, bg="#000000")
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(col2, text="[ DESTINATION ]", font=("Helvetica", 8, "bold"), fg="#ffff00", bg="#000000").pack(anchor="nw", padx=10)
        self.inspect_text_dest = tk.Text(col2, bg="#000000", fg="#ffff00", font=("Courier", 9), bd=0, highlightthickness=0)
        self.inspect_text_dest.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # --- KEY / LEGEND (Right Sidebar) ---
        self.legend_frame = tk.Frame(self.inspect_split, bg="#1a1a1a", bd=1, relief="raised", width=200)
        self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.legend_frame.pack_propagate(False)
        
        tk.Label(self.legend_frame, text="🗝️ SYMBOL KEY", font=("Helvetica", 9, "bold"), fg="#ffffff", bg="#333333").pack(fill=tk.X)
        
        symbols = [
            ("🚀", "PUSH", "Network Out"),
            ("💾", "CACHE", "State Registry"),
            ("Ⓖ", "GUI", "Local Interface"),
            ("🅾️", "OSC", "OSC Protocol"),
            ("🎹", "MIDI", "MIDI Hardware"),
            ("Ⓜ️", "MQTT", "Broker Reflect"),
            ("Ⓢ", "SNMP", "Network Infra"),
            ("🔗", "LINK", "Splink Active")
        ]
        for sym, name, desc in symbols:
            f = tk.Frame(self.legend_frame, bg="#1a1a1a")
            f.pack(fill=tk.X, padx=5, pady=1)
            tk.Label(f, text=sym, font=("Helvetica", 10), fg="#00ff00", bg="#1a1a1a", width=2).pack(side=tk.LEFT)
            tk.Label(f, text=f"{name: <6}", font=("Courier", 8, "bold"), fg="#888888", bg="#1a1a1a").pack(side=tk.LEFT)
            tk.Label(f, text=desc, font=("Helvetica", 7), fg="#666666", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        tk.Label(self.legend_frame, text="🎨 COLOR KEY", font=("Helvetica", 9, "bold"), fg="#ffffff", bg="#333333").pack(fill=tk.X, pady=(10, 0))
        
        colors = [
            ("HERE", "#00ff00", None, "This Machine"),
            ("REMOTE", "yellow", "#440000", "Other Machine"),
            ("MUTATION", "red", "#440000", "Hardware Ctrl"),
            ("MIDI", "#ff00ff", None, "MIDI Traffic"),
            ("OSC", "#00ffff", None, "OSC Traffic"),
            ("SYSTEM", "#888888", None, "Internal/Init"),
            ("SPLINK", "#a0a0a0", "#1a1a1a", "Brokered Link")
        ]
        for name, fg, bg, desc in colors:
            f = tk.Frame(self.legend_frame, bg="#1a1a1a")
            f.pack(fill=tk.X, padx=5, pady=1)
            lbl = tk.Label(f, text=name, font=("Courier", 8, "bold"), fg=fg, bg=bg if bg else "#1a1a1a", width=8)
            lbl.pack(side=tk.LEFT)
            tk.Label(f, text=desc, font=("Helvetica", 7), fg="#666666", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        # 3. Footer
        btn_frame = tk.Frame(self, bg="#2b2b2b")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Clear Firehose", command=self.clear_log).pack(side=tk.LEFT, padx=20)
        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_frame, text="Auto-Scroll", variable=self.autoscroll_var).pack(side=tk.LEFT)

    def _setup_protocol_matrix(self):
        """Creates the matrix of checkboxes to enable/disable protocol inputs and outputs."""
        self.matrix = ProtocolMatrix(self)
        self.matrix.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 10))

    def on_router_event(self, msg):
        """Callback from ProtocolRouter ingest loop."""
        self.after(0, lambda: self._add_entry(msg))

    def _add_entry(self, msg):
        if not self.tree.winfo_exists(): return

        # Machine Time (UTP)
        utp = f"{msg['ts']:.6f}"
        source = msg["source"]             # Transport (e.g. MQTT)
        logical_source = msg.get("logical_source", source) # Identity (e.g. MIDI)
        guid = msg.get("logical_guid", msg["guid"])        # Identity (e.g. 32_0/3)
        
        strategy = msg.get("strategy", "BROADCAST")
        topic = msg["topic"]
        val = msg["val"]
        
        # Tags are now pre-calculated by the router (no brains in GUI)
        tags = msg.get("ui_tags", [])

        # ⚡ DISPLAY ENRICHMENT: Add emoji for visual confirmation in the tree ONLY
        display_source = logical_source
        if "SPLINK" in tags:
            display_source = f"🔗 {logical_source}"

        # ⚡ STACK BEHAVIOR: Insert at TOP (index 0)
        item_id = self.tree.insert("", 0, values=(utp, display_source, guid, strategy, topic, val), tags=tuple(tags))
        
        if len(self.tree.get_children()) > 100:
            self.tree.delete(self.tree.get_children()[-1])

        # If autoscroll is on, make sure the latest (top) is visible
        if self.autoscroll_var.get():
            self.tree.see(item_id)

    def on_select_packet(self, event):
        """Populates the investigation pane and handles SPLINK selection logic."""
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        utp = item["values"][0]
        topic = item["values"][4]
        tags = item["tags"]

        # ⚡ AUTO-DUAL: If this is a splinked message, try to find and show BOTH halves
        if "SPLINK" in tags:
            trigger_ts, result_ts = self.router.get_splink_relationship(utp)
            if trigger_ts and result_ts:
                self._src_utp = f"{trigger_ts:.6f}"
                self._dest_utp = f"{result_ts:.6f}"
                # Update Entries
                item_src = self._find_item_by_ts(self._src_utp)
                item_dest = self._find_item_by_ts(self._dest_utp)
                if item_src: self.src_var.set(item_src["values"][4])
                if item_dest: self.dest_var.set(item_dest["values"][4])
                self.splink_btn.configure(fg="#00ff00")
                self._refresh_investigation()
                return

        # ⚡ STANDARD ALTERNATING LOGIC (for non-splinked messages)
        if not self.src_var.get():
            self.src_var.set(topic)
            self._src_utp = utp
            self.splink_btn.configure(fg="#888888")
        elif not self.dest_var.get():
            if topic != self.src_var.get():
                self.dest_var.set(topic)
                self._dest_utp = utp
                self.splink_btn.configure(fg="#00ff00")
            else:
                self.src_var.set("")
                self._src_utp = None
        else:
            # Shift
            self.src_var.set(self.dest_var.get())
            self._src_utp = getattr(self, "_dest_utp", None)
            self.dest_var.set(topic)
            self._dest_utp = utp

        self._refresh_investigation()

    def _find_item_by_ts(self, ts_str):
        """Helper to find tree item by timestamp value."""
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if values and values[0] == ts_str:
                return self.tree.item(item)
        return None

    def _refresh_investigation(self):
        """Updates the text widgets based on current selection timestamps."""
        self.inspect_text_src.delete("1.0", tk.END)
        self.inspect_text_dest.delete("1.0", tk.END)

        if hasattr(self, "_src_utp") and self._src_utp:
            report_src = self.router.get_dpi_report(self._src_utp)
            self.inspect_text_src.insert(tk.END, report_src)
            
        if hasattr(self, "_dest_utp") and self._dest_utp:
            report_dest = self.router.get_dpi_report(self._dest_utp)
            self.inspect_text_dest.insert(tk.END, report_dest)

    def create_direct_splink(self):
        """Sends command to Router to create the link and navigates to Splinker UI."""
        src = self.src_var.get()
        dest = self.dest_var.get()
        
        # ⚡ TIE TOGETHER: Extract the exact values the user is investigating
        src_val = self._get_val_from_utp(self._src_utp) if self._src_utp else None
        dest_val = self._get_val_from_utp(self._dest_utp) if self._dest_utp else None

        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔗 CommandRouter: SPLINK button clicked. Source='{src}' ({src_val}), Dest='{dest}' ({dest_val})", "INFO")
        
        if not src or not dest: 
            logger.warning("🔗 CommandRouter: Cannot splink, source or destination is empty!")
            return
        
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔗 CommandRouter: Calling router.publish_splink...", "DEBUG")
        if self.router.publish_splink(src, dest, s_val=src_val, d_val=dest_val):
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔗 CommandRouter: Splink command published successfully.", "SUCCESS")
            # Visual feedback
            self.splink_btn.configure(text="✅ CREATED", fg="#00ff00")
            
            # ⚡ NAVIGATION: Switch to Splinker Tab
            app = self._find_app_instance()
            if app:
                app.show_splinker_tab(src_topic=src, dest_topic=dest)
                
            self.after(2000, lambda: self._reset_splink_selection())

    def _get_val_from_utp(self, utp):
        """Finds the raw value for a specific machine time in the firehose."""
        if not utp: return None
        with self.router.monitor._firehose_lock:
            match = next((m for m in self.router.firehose if f"{m['ts']:.6f}" == utp), None)
            return match["val"] if match else None

    def _find_app_instance(self):
        from oaGui.Managers.gui_display import Application
        curr = self.master
        while curr:
            if isinstance(curr, Application):
                return curr
            try:
                curr = curr.master
            except:
                break
        return None

    def _reset_splink_selection(self):
        self.src_var.set("")
        self.dest_var.set("")
        self.splink_btn.configure(text="🔗 SPLINK", fg="#888888")

    def clear_log(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        with self.router.monitor._firehose_lock:
            self.router.firehose.clear()

    def destroy(self):
        if self.router:
            try: self.router._observers.remove(self.on_router_event)
            except: pass
        super().destroy()

def get_gui_class():
    return CommandRouter
