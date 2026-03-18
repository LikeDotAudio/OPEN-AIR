# oaGuiDefinitions/right_50/bottom_90/4_Splinker/111_Logs/gui_splinker_logs.py
#
# Log viewer for Splinker activity.
#
# Author: Anthony P. Kuzub(Splinker Protocol)
# Version 20260311.Logs.1

import tkinter as tk
from tkinter import ttk
import orjson
import time
from loguru import logger
from oaSplinker.splinker import ControlBroker

class SplinkerLogs(tk.Frame):
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        super().__init__(parent, **kwargs)
        
        self.splinker_manager = ControlBroker.get_instance()
        app = self.config_data.get("app_instance")
        self.mqtt_manager = app.mqtt_connection_manager if app else None
        self.subscriber_router = self.config_data.get("subscriber_router")
        
        self.event_cache = {} # ts -> event_data
        self.pending_events = [] # Buffer for throttling
        self._update_scheduled = False
        self.is_visible = True
        
        self._setup_ui()
        
        self.splinker_manager.add_monitor_callback(self.handle_splinker_event)

        # ⚡ VISIBILITY TRACKING: Bind to Map/Unmap to pause updates
        self.bind("<Map>", lambda e: self._set_visibility(True))
        self.bind("<Unmap>", lambda e: self._set_visibility(False))

    def _set_visibility(self, visible):
        self.is_visible = visible
        if visible and self.pending_events and not self._update_scheduled:
            self._schedule_update()

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")
        
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- TOP: Treeview ---
        tree_container = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(tree_container, weight=3)

        tk.Label(tree_container, text="📡 LIVE BROKERAGE FEED", bg="#2b2b2b", fg="#00ff00", font=("Helvetica", 10, "bold")).pack(anchor="w")
        
        cols = ("Time", "Label", "Dir", "Source Topic", "Dest Topic", "In", "Out")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=10)
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor="center")
        
        self.tree.column("Source Topic", width=200, anchor="w")
        self.tree.column("Dest Topic", width=200, anchor="w")
        self.tree.column("Time", width=120)
        
        # ⚡ OPTIMIZATION: Configure tags ONCE at setup
        self.tree.tag_configure("FORWARD", foreground="#00ff00")
        self.tree.tag_configure("REVERSE", foreground="#ffff00")

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select_event)

        # --- BOTTOM: Investigation ---
        inspect_container = tk.Frame(self.paned, bg="#000000", bd=1, relief="sunken")
        self.paned.add(inspect_container, weight=2)

        tk.Label(inspect_container, text="🔍 SPLINK PACKET INVESTIGATION", font=("Helvetica", 10, "bold"), fg="#888888", bg="#000000").pack(anchor="nw", padx=5)
        self.inspect_text = tk.Text(inspect_container, bg="#000000", fg="cyan", font=("Courier", 10), bd=0, highlightthickness=0)
        self.inspect_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def handle_splinker_event(self, msg_type, data):
        if msg_type == "splink_event":
            # ⚡ THROTTLING: Buffer events and schedule batch update
            self.pending_events.append(data)
            if not self._update_scheduled and self.is_visible:
                self._schedule_update()
        elif msg_type == "debug_log":
            pass

    def _schedule_update(self):
        if not self.winfo_exists(): return
        self._update_scheduled = True
        # Update every 100ms to keep UI responsive under heavy load
        self.after(100, self._process_pending_events)

    def _process_pending_events(self):
        self._update_scheduled = False
        if not self.winfo_exists() or not self.is_visible: return
        
        if not self.pending_events: return
        
        # Take a chunk (max 50 per update to keep frame rate high)
        chunk = self.pending_events[:50]
        self.pending_events = self.pending_events[50:]
        
        for event in chunk:
            self._add_tree_entry(event)
            
        # If more events remain, schedule next batch
        if self.pending_events:
            self._schedule_update()

    def _add_tree_entry(self, event):
        if not self.tree.winfo_exists(): return
        
        ts_str = f"{event['ts']:.6f}"
        self.event_cache[ts_str] = event
        
        tags = (event["direction"],)

        # Truncate values for the tree display (safety)
        val_in = str(event.get("input_val", "N/A"))
        val_out = str(event.get("output_val", "N/A"))
        
        self.tree.insert("", 0, values=(
            ts_str,
            event["label"],
            "FWD" if event["direction"] == "FORWARD" else "REV",
            event["source"],
            event["dest"],
            val_in[:40],
            val_out[:40]
        ), tags=tags)

        # Trim tree
        if len(self.tree.get_children()) > 200:
            children = self.tree.get_children()
            # Delete oldest batch for performance
            for i in range(min(5, len(children) - 200)):
                last_item = children[-(i+1)]
                last_ts = self.tree.item(last_item)["values"][0]
                if last_ts in self.event_cache: del self.event_cache[last_ts]
                self.tree.delete(last_item)

    def on_select_event(self, event):
        selected = self.tree.selection()
        if not selected: return
        
        try:
            ts_str = self.tree.item(selected[0])["values"][0]
            event_data = self.event_cache.get(ts_str)
            if event_data:
                self._refresh_investigation(event_data)
        except (IndexError, KeyError):
            pass

    def _refresh_investigation(self, event):
        self.inspect_text.delete("1.0", tk.END)
        
        def _safe_str(val, limit=2000):
            s = str(val)
            if len(s) > limit:
                return s[:limit] + f"\n... [TRUNCATED {len(s)-limit} chars]"
            return s

        report = []
        report.append(f"╔════════════════════════════════════════════════════════════════════════════════")
        report.append(f"║ 🔗 SPLINK INVESTIGATION REPORT")
        report.append(f"╠════════════════════════════════════════════════════════════════════════════════")
        report.append(f"║ ID:        {event['splink_id']}")
        report.append(f"║ Label:     {event['label']}")
        report.append(f"║ Time:      {time.ctime(event['ts'])} ({event['ts']:.6f})")
        report.append(f"║ Direction: {event['direction']}")
        
        guid = event.get("guid", "N/A")
        report.append(f"║ GUID:      {guid}")
        
        if "orig_guid" in event:
            report.append(f"║ TRIGGER:   {event['orig_guid']} @ {event.get('orig_ts', 'Unknown')}")

        report.append(f"╠────────────────────────────────────────────────────────────────────────────────")
        report.append(f"║ SOURCE:    {event['source']}")
        report.append(f"║ DEST:      {event['dest']}")
        report.append(f"╠────────────────────────────────────────────────────────────────────────────────")
        report.append(f"║ INPUT:     {_safe_str(event['input_val'])}")
        
        if "steps" in event and event["steps"]:
            report.append(f"║")
            report.append(f"║ 🛠️ TRANSFORMATION PIPELINE:")
            for i, step in enumerate(event["steps"]):
                report.append(f"║   Step {i+1}: {step['handler']}")
                report.append(f"║          {_safe_str(step['in'], 200)} ➔ {_safe_str(step['out'], 200)}")
        
        report.append(f"║")
        if "terminated_by" in event:
            report.append(f"║ 🛑 TERMINATED BY: {event['terminated_by']}")
        else:
            report.append(f"║ OUTPUT:    {_safe_str(event.get('output_val', 'N/A'))}")
            
        report.append(f"╚════════════════════════════════════════════════════════════════════════════════")
        
        self.inspect_text.insert(tk.END, "\n".join(report))

    def destroy(self):
        self.splinker_manager.remove_monitor_callback(self.handle_splinker_event)
        super().destroy()

def get_gui_class():
    return SplinkerLogs
