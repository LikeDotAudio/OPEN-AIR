import inspect

# 3_Command_Router/command_router.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose
import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
from loguru import logger

from oaComBroker.Core.protocol_router.manager import ProtocolRouter
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

class CommandRouterLegend(tk.Frame):
    """Encapsulates the symbol and color key sidebar."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1a1a1a", bd=1, relief="raised", width=200, **kwargs)
        self.pack_propagate(False)
        self._setup_sections()

    def _setup_sections(self):
        tk.Label(self, text="🗝️ SYMBOL KEY", font=("Helvetica", 9, "bold"), fg="#ffffff", bg="#333333").pack(fill=tk.X)
        symbols = [("🚀", "PUSH", "Network Out"), ("💾", "CACHE", "State Registry"), ("Ⓖ", "GUI", "Local Interface"), ("🅾️", "OSC", "OSC Protocol"), ("🎹", "MIDI", "MIDI Hardware"), ("Ⓜ️", "MQTT", "Broker Reflect"), ("Ⓢ", "SNMP", "Network Infra"), ("🔗", "LINK", "Splink Active")]
        for sym, name, desc in symbols:
            f = tk.Frame(self, bg="#1a1a1a"); f.pack(fill=tk.X, padx=5, pady=1)
            tk.Label(f, text=sym, font=("Helvetica", 10), fg="#00ff00", bg="#1a1a1a", width=2).pack(side=tk.LEFT)
            tk.Label(f, text=f"{name: <6}", font=("Courier", 8, "bold"), fg="#888888", bg="#1a1a1a").pack(side=tk.LEFT)
            tk.Label(f, text=desc, font=("Helvetica", 7), fg="#666666", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

        tk.Label(self, text="🎨 COLOR KEY", font=("Helvetica", 9, "bold"), fg="#ffffff", bg="#333333").pack(fill=tk.X, pady=(10, 0))
        colors = [("HERE", "#00ff00", None, "This Machine"), ("REMOTE", "yellow", "#440000", "Other Machine"), ("MUTATION", "red", "#440000", "Hardware Ctrl"), ("MIDI", "#ff00ff", None, "MIDI Traffic"), ("OSC", "#00ffff", None, "OSC Traffic"), ("SYSTEM", "#888888", None, "Internal/Init"), ("SPLINK", "#a0a0a0", "#1a1a1a", "Brokered Link")]
        for name, fg, bg, desc in colors:
            f = tk.Frame(self, bg="#1a1a1a"); f.pack(fill=tk.X, padx=5, pady=1)
            tk.Label(f, text=name, font=("Courier", 8, "bold"), fg=fg, bg=bg or "#1a1a1a", width=8).pack(side=tk.LEFT)
            tk.Label(f, text=desc, font=("Helvetica", 7), fg="#666666", bg="#1a1a1a").pack(side=tk.LEFT, padx=5)

class CommandInvestigationPane(tk.Frame):
    """Encapsulates the dual-packet inspection logic."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#000000", bd=1, relief="sunken", **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        tk.Label(self, text="🔍 DUAL PACKET INVESTIGATION & SPLINK DISCOVERY", font=("Helvetica", 10, "bold"), fg="#888888", bg="#000000").pack(side=tk.TOP, anchor="nw", padx=5)
        split_frame = tk.Frame(self, bg="#000000")
        split_frame.pack(fill=tk.BOTH, expand=True)

        self.text_src = self._create_inspector(split_frame, "[ SOURCE ]", "#00ff00")
        self.text_dest = self._create_inspector(split_frame, "[ DESTINATION ]", "#ffff00")
        self.legend = CommandRouterLegend(split_frame)
        self.legend.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_inspector(self, parent, title, color):
        col = tk.Frame(parent, bg="#000000")
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(col, text=title, font=("Helvetica", 8, "bold"), fg=color, bg="#000000").pack(anchor="nw", padx=10)
        text = tk.Text(col, bg="#000000", fg=color, font=("Courier", 9), bd=0, highlightthickness=0)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        return text

    def update_inspectors(self, src_data, dest_data):
        """Updates text widgets with formatted JSON data."""
        self.text_src.delete("1.0", tk.END)
        self.text_dest.delete("1.0", tk.END)
        if src_data: self.text_src.insert(tk.END, src_data)
        if dest_data: self.text_dest.insert(tk.END, dest_data)

class CommandRouter(tk.Frame):
    """Centralized Hub-and-Spoke Command Monitor."""
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        super().__init__(parent, **kwargs)
        self.router = ProtocolRouter.get_instance()
        self.src_var = tk.StringVar(value="")
        self.dest_var = tk.StringVar(value="")
        self._setup_ui()
        self.router.register_cache_observer(self.on_router_event)

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")
        self._setup_header()
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._setup_monitor_pane()
        self.investigation_pane = CommandInvestigationPane(self.paned)
        self.paned.add(self.investigation_pane, weight=2)
        self._setup_footer()

    def _setup_header(self):
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="🌐 COMMAND ROUTER & INVESTIGATION", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        tk.Label(header, textvariable=tk.StringVar(value=f"Instance Identity: {self.router.GUID}"), font=("Courier", 10, "bold"), fg="#00ff00", bg="#2b2b2b").pack(side=tk.RIGHT, padx=20)

    def _setup_monitor_pane(self):
        container = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(container, weight=3)
        self._initialize_treeview(container)
        self._setup_splink_bar(container)

    def _initialize_treeview(self, parent):
        frame = tk.Frame(parent, bg="#2b2b2b"); frame.pack(fill=tk.BOTH, expand=True)
        cols = ("Machine Time", "Source", "GUID", "Strategy", "Topic", "Value")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self._configure_tree_tags()
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_packet)

    def _configure_tree_tags(self):
        tags = {"HERE": ("#00ff00", None), "REMOTE": ("yellow", "#440000"), "MIDI": ("#ff00ff", None), "OSC": ("#00ffff", None), "MUTATION": ("red", "#440000"), "SYSTEM": ("#888888", None), "SPLINK": ("#a0a0a0", "#1a1a1a")}
        for tag, (fg, bg) in tags.items(): self.tree.tag_configure(tag, foreground=fg, background=bg)

    def _setup_splink_bar(self, parent):
        bar = tk.Frame(parent, bg="#1a1a1a", pady=5); bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(bar, text="SPLINK:", font=("Helvetica", 10, "bold"), fg="#888888", bg="#1a1a1a").pack(side=tk.LEFT, padx=10)
        tk.Entry(bar, textvariable=self.src_var, bg="#000000", fg="#00ff00", width=40, bd=1).pack(side=tk.LEFT, padx=5)
        self.splink_btn = tk.Button(bar, text="🔗 SPLINK", command=self.create_direct_splink, bg="#2b2b2b", fg="#888888", font=("Helvetica", 10, "bold"), padx=10)
        self.splink_btn.pack(side=tk.LEFT, padx=10)
        tk.Entry(bar, textvariable=self.dest_var, bg="#000000", fg="#ffff00", width=40, bd=1).pack(side=tk.LEFT, padx=5)

    def _setup_footer(self):
        footer = tk.Frame(self, bg="#2b2b2b"); footer.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        ttk.Button(footer, text="Clear Firehose", command=self.clear_log).pack(side=tk.LEFT, padx=20)
        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(footer, text="Auto-Scroll", variable=self.autoscroll_var).pack(side=tk.LEFT)

    def on_router_event(self, message):
        self.after(0, lambda: self._add_entry(message))

    def _add_entry(self, message):
        if not self.tree.winfo_exists(): return
        utp, source, guid = f"{message['timestamp']:.6f}", message.get("logical_source", message["source"]), message.get("logical_guid", message.get("guid", "UNKNOWN"))
        display_source = f"🔗 {source}" if "SPLINK" in message.get("ui_tags", []) else source
        item_id = self.tree.insert("", 0, values=(utp, display_source, guid, message.get("strategy", "BROADCAST"), message["topic"], message["value"]), tags=tuple(message.get("ui_tags", [])))
        if len(self.tree.get_children()) > 100: self.tree.delete(self.tree.get_children()[-1])
        if self.autoscroll_var.get(): self.tree.see(item_id)

    def on_select_packet(self, event):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        utp, topic, tags = item["values"][0], item["values"][4], item["tags"]
        if "SPLINK" in tags:
            t_ts, r_ts = self.router.get_splink_relationship(utp)
            if t_ts and r_ts:
                self._src_utp, self._dest_utp = f"{t_ts:.6f}", f"{r_ts:.6f}"
                i_src, i_dest = self._find_item_by_ts(self._src_utp), self._find_item_by_ts(self._dest_utp)
                if i_src: self.src_var.set(i_src["values"][4])
                if i_dest: self.dest_var.set(i_dest["values"][4])
                self.splink_btn.configure(fg="#00ff00")
                self._refresh_investigation(); return
        if not self.src_var.get(): self._src_utp = utp; self.src_var.set(topic); self.splink_btn.configure(fg="#888888")
        elif not self.dest_var.get() and topic != self.src_var.get(): self._dest_utp = utp; self.dest_var.set(topic); self.splink_btn.configure(fg="#00ff00")
        else: self.src_var.set(self.dest_var.get()); self._src_utp = getattr(self, "_dest_utp", None); self.dest_var.set(topic); self._dest_utp = utp
        self._refresh_investigation()

    def _find_item_by_ts(self, ts):
        for item in self.tree.get_children():
            if self.tree.item(item)["values"][0] == ts: return self.tree.item(item)
        return None

    def _refresh_investigation(self):
        try: import orjson; has_orjson = True
        except ImportError: import json; has_orjson = False
        src_pretty, dest_pretty = "", ""
        if hasattr(self, "_src_utp") and self._src_utp:
            m = self.router.get_message_by_utp(self._src_utp)
            if m: src_pretty = orjson.dumps(m, option=orjson.OPT_INDENT_2).decode() if has_orjson else json.dumps(m, indent=2)
        if hasattr(self, "_dest_utp") and self._dest_utp:
            m = self.router.get_message_by_utp(self._dest_utp)
            if m: dest_pretty = orjson.dumps(m, option=orjson.OPT_INDENT_2).decode() if has_orjson else json.dumps(m, indent=2)
        self.investigation_pane.update_inspectors(src_pretty, dest_pretty)

    def create_direct_splink(self):
        src, dest = self.src_var.get(), self.dest_var.get()
        if not src or not dest: return
        s_val, d_val = self._get_val_from_utp(getattr(self, "_src_utp", None)), self._get_val_from_utp(getattr(self, "_dest_utp", None))
        if self.router.publish_splink(src, dest, s_val=s_val, d_val=d_val):
            self.splink_btn.configure(text="✅ CREATED", fg="#00ff00")
            app = self._find_app_instance()
            if app: app.show_splinker_tab(src_topic=src, dest_topic=dest)
            self.after(2000, lambda: self._reset_splink_selection())

    def _get_val_from_utp(self, utp):
        if not utp: return None
        with self.router.monitor._firehose_lock:
            m = next((m for m in self.router.firehose if f"{m['timestamp']:.6f}" == utp), None)
            return m["value"] if m else None

    def _find_app_instance(self):
        from oaGui.Managers.gui_display import Application
        curr = self.master
        while curr:
            if isinstance(curr, Application): return curr
            try: curr = curr.master
            except: break
        return None

    def _reset_splink_selection(self):
        self.src_var.set(""); self.dest_var.set(""); self.splink_btn.configure(text="🔗 SPLINK", fg="#888888")

    def clear_log(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        with self.router.monitor._firehose_lock: self.router.firehose.clear()

    def destroy(self):
        if self.router:
            try: self.router._observers.remove(self.on_router_event)
            except: pass
        super().destroy()

    def on_router_event(self, message):
        """Callback from ProtocolRouter ingest loop."""
        self.after(0, lambda: self._add_entry(message))

    def _add_entry(self, message):
        if not self.tree.winfo_exists(): return

        # Machine Time (UTP)
        utp = f"{message['timestamp']:.6f}"
        source = message["source"]             # Transport (e.g. MQTT)
        logical_source = message.get("logical_source", source) # Identity (e.g. MIDI)
        # ⚡ V3.1.5 HARDENING: Ensure 'guid' exists before access to prevent Tkinter KeyError
        guid = message.get("logical_guid", message.get("guid", "UNKNOWN"))

        strategy = message.get("strategy", "BROADCAST")
        topic = message["topic"]
        value = message["value"]

        # Tags are now pre-calculated by the router (no brains in GUI)
        tags = message.get("ui_tags", [])

        # ⚡ DISPLAY ENRICHMENT: Add emoji for visual confirmation in the tree ONLY
        display_source = logical_source
        if "SPLINK" in tags:
            display_source = f"🔗 {logical_source}"

        # ⚡ STACK BEHAVIOR: Insert at TOP (index 0)
        item_id = self.tree.insert("", 0, values=(utp, display_source, guid, strategy, topic, value), tags=tuple(tags))

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

        try:
            import orjson
            has_orjson = True
        except ImportError:
            import json
            has_orjson = False

        if hasattr(self, "_src_utp") and self._src_utp:
            message_src = self.router.get_message_by_utp(self._src_utp)
            if message_src:
                if has_orjson:
                    pretty_str = orjson.dumps(message_src, option=orjson.OPT_INDENT_2).decode()
                else:
                    pretty_str = json.dumps(message_src, indent=2)
                self.inspect_text_src.insert(tk.END, pretty_str)

        if hasattr(self, "_dest_utp") and self._dest_utp:
            message_dest = self.router.get_message_by_utp(self._dest_utp)
            if message_dest:
                if has_orjson:
                    pretty_str = orjson.dumps(message_dest, option=orjson.OPT_INDENT_2).decode()
                else:
                    pretty_str = json.dumps(message_dest, indent=2)
                self.inspect_text_dest.insert(tk.END, pretty_str)

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

        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔗 CommandRouter: Calling router.publish_splink...", "DEBUG")
        if self.router.publish_splink(src, dest, s_val=src_val, d_val=dest_val):
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🔗 CommandRouter: Splink command published successfully.", "SUCCESS")
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
            match = next((m for m in self.router.firehose if f"{m['timestamp']:.6f}" == utp), None)
            return match["value"] if match else None

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
