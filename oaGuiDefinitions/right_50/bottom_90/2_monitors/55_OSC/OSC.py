import tkinter as tk
from tkinter import ttk
import datetime

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger

class OscDashboard(tk.Frame):
    """
    OSC Status & Monitor.
    A pure observer that reflects state from the OSCManager worker.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        self.osc_manager = self._find_osc_manager(parent)
        
        if not self.osc_manager:
            logger.warning("🅾️ OscDashboard: Could not find OSCManager. Monitor will be inactive.")
        else:
            logger.info("🅾️ OscDashboard: OSCManager linked successfully.")
        
        # Activity cache for investigation: { ts_ms_str: msg_dict }
        self._activity_cache = {}
        
        self._setup_ui()
        
        if self.osc_manager:
            self.osc_manager.add_monitor_callback(self.on_osc_activity)
            self._refresh_ui()

    def _find_osc_manager(self, widget):
        # 1. Try config_data first (Direct Injection)
        if "osc_manager" in self.config_data:
            return self.config_data["osc_manager"]
            
        if "app_instance" in self.config_data:
            app = self.config_data["app_instance"]
            if hasattr(app, "osc_manager"):
                return app.osc_manager

        # 2. Hierarchy Search (Fallback)
        from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder) and hasattr(curr, 'app_instance'):
                app = getattr(curr, 'app_instance')
                if hasattr(app, 'osc_manager'):
                    return app.osc_manager
            try: curr = curr.master
            except: break
        return None

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="🅾️ OSC CONTROL HUB", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        self.status_lbl = tk.Label(header, text="Status: DISCONNECTED", font=("Courier", 10, "bold"), fg="#ff4444", bg="#2b2b2b")
        self.status_lbl.pack(side=tk.RIGHT, padx=20)

        # 2. Split View (Monitor + Investigation)
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
        self.tree.tag_configure("RX", foreground="#aa00ff") # Purple
        self.tree.tag_configure("TX", foreground="#ff00ff") # Magenta

        vsb = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_packet)

        # --- BOTTOM: Investigation Pane ---
        inspect_frame = tk.Frame(self.paned, bg="#000000", bd=1, relief="sunken")
        self.paned.add(inspect_frame, weight=2)

        tk.Label(inspect_frame, text="🔍 OSC MESSAGE DISSECTOR", font=("Helvetica", 10, "bold"), fg="#888888", bg="#000000").pack(anchor="nw", padx=5)
        
        self.inspect_text = tk.Text(inspect_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), bd=0, highlightthickness=0)
        self.inspect_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.inspect_text.tag_configure("header", foreground="#ffffff", font=("Courier", 10, "bold"))

        # 3. Bottom Port Status
        status_frame = tk.LabelFrame(self, text="Network & Routing Status", bg="#2b2b2b", fg="#888888")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False, padx=15, pady=10)

        self.info_tree = ttk.Treeview(status_frame, columns=("Value"), show="tree", height=4)
        self.info_tree.heading("#0", text="Property")
        self.info_tree.column("#0", width=200)
        self.info_tree.pack(fill=tk.X, expand=True, padx=5, pady=5)

    def _refresh_ui(self):
        """Pure UI refresh. Pulls all data from the OSC Manager worker."""
        if not self.osc_manager: return
        
        status = self.osc_manager.get_status()
        
        # Update Header
        if status["running"]:
            self.status_lbl.configure(text=f"ACTIVE: {status['rx_socket']}", fg="#00ff00")
        else:
            self.status_lbl.configure(text="OFFLINE", fg="#ff4444")

        # Update Detail Tree
        for item in self.info_tree.get_children():
            self.info_tree.delete(item)
            
        self.info_tree.insert("", "end", text="RX Socket", values=(status["rx_socket"],))
        self.info_tree.insert("", "end", text="TX Socket", values=(status["tx_socket"],))
        self.info_tree.insert("", "end", text="Active Routes", values=(status["routes_count"],))
        self.info_tree.insert("", "end", text="Bridge Mode", values=("Enabled" if status["bridge_mode"] else "Observer Only",))

    def on_osc_activity(self, direction, address, value, topic=None):
        """Called by the manager when traffic occurs or status changes."""
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


    def destroy(self):
        if self.osc_manager:
            try: self.osc_manager.remove_monitor_callback(self.on_osc_activity)
            except: pass
        super().destroy()

def get_gui_class():
    return OscDashboard
