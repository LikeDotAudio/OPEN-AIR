# oaGuiDefinitions/right_50/bottom_90/4_Splinker/222_Editor/gui_splinker_editor.py
#
# Splinker UI for managing brokerage connections.
#
# Author: Anthony P. Kuzub(Splinker Protocol)
# Version 20260311.Editor.1

import tkinter as tk
from tkinter import ttk, messagebox
import orjson
from loguru import logger
from oaSplinker.splinker import ControlBroker

class SplinkerEditor(tk.Frame):
    def __init__(self, parent, **kwargs):
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        super().__init__(parent, **kwargs)
        
        self.splinker_manager = ControlBroker.get_instance()
        app = self.config_data.get("app_instance")
        self.mqtt_manager = app.mqtt_connection_manager if app else None
        self.state_cache_manager = app.state_cache_manager if app else None
        
        from oaComBroker.protocol_router import ProtocolRouter
        self.router = ProtocolRouter.get_instance()
        
        self._setup_ui()
        
        if self.mqtt_manager:
            self.mqtt_manager.subscribe("OPEN-AIR/System/Status/Splinker/List", self.handle_splinker_status)
            self.mqtt_manager.subscribe("OPEN-AIR/System/Status/Splinker/Panic", self.handle_panic_status)
        
        self.refresh_splink_list()
        self.selected_splink_id = None

    def _setup_ui(self):
        self.configure(bg="#2b2b2b")

        # Main Paned Window (Top: Editor, Bottom: List)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- TOP: Editor ---
        self.editor_frame = tk.LabelFrame(self.paned, text="Splink Editor & Scaling", bg="#2b2b2b", fg="#888888", padx=10, pady=10)
        self.paned.add(self.editor_frame, weight=1)
        
        tk.Label(self.editor_frame, text="SOURCE PATH (Topic or Topic:Key):", fg="#00ff00", bg="#2b2b2b").pack(anchor="w")
        self.src_entry = tk.Entry(self.editor_frame, bg="#000000", fg="#00ff00", insertbackground="white")
        self.src_entry.pack(fill=tk.X, pady=2)
        
        tk.Label(self.editor_frame, text="DESTINATION PATH (Topic or Topic:Key):", fg="#ffff00", bg="#2b2b2b").pack(anchor="w")
        self.dest_entry = tk.Entry(self.editor_frame, bg="#000000", fg="#ffff00", insertbackground="white")
        self.dest_entry.pack(fill=tk.X, pady=2)

        # Mode Selection
        mode_frame = tk.LabelFrame(self.editor_frame, text="Communication Mode", bg="#2b2b2b", fg="#888888", pady=5)
        mode_frame.pack(fill=tk.X, pady=5)
        self.mode_var = tk.StringVar(value="SPLINK")
        
        modes = [
            ("SPLICE", "Source ➔ Dest (One-way forward)"),
            ("LINK", "Dest ➔ Source (Feedback loop)"),
            ("SPLINK", "Source ⇄ Dest (Bidirectional sync)")
        ]
        
        for i, (m, desc) in enumerate(modes):
            tk.Radiobutton(mode_frame, text=m, variable=self.mode_var, value=m, bg="#2b2b2b", fg="white", selectcolor="#444444", font=("Helvetica", 9, "bold")).grid(row=i, column=0, sticky="w", padx=10)
            tk.Label(mode_frame, text=desc, bg="#2b2b2b", fg="#aaaaaa", font=("Helvetica", 8, "italic")).grid(row=i, column=1, sticky="w", padx=5)

        # Scaling Handler Section
        scale_frame = tk.LabelFrame(self.editor_frame, text="Scaling / Mapping", bg="#2b2b2b", fg="#888888", pady=5)
        scale_frame.pack(fill=tk.X, pady=10)
        grid_frame = tk.Frame(scale_frame, bg="#2b2b2b")
        grid_frame.pack()
        
        tk.Label(grid_frame, text="Src Min", bg="#2b2b2b", fg="white").grid(row=0, column=0)
        self.s_min = tk.Entry(grid_frame, width=8, bg="#000000", fg="#00ff00")
        self.s_min.grid(row=1, column=0, padx=2)
        
        tk.Label(grid_frame, text="Src Max", bg="#2b2b2b", fg="white").grid(row=0, column=1)
        self.s_max = tk.Entry(grid_frame, width=8, bg="#000000", fg="#00ff00")
        self.s_max.grid(row=1, column=1, padx=2)
        
        tk.Label(grid_frame, text="➜", bg="#2b2b2b", fg="white", font=("bold")).grid(row=1, column=2, padx=10)
        
        tk.Label(grid_frame, text="Dest Min", bg="#2b2b2b", fg="white").grid(row=0, column=3)
        self.d_min = tk.Entry(grid_frame, width=8, bg="#000000", fg="#ffff00")
        self.d_min.grid(row=1, column=3, padx=2)
        
        tk.Label(grid_frame, text="Dest Max", bg="#2b2b2b", fg="white").grid(row=0, column=4)
        self.d_max = tk.Entry(grid_frame, width=8, bg="#000000", fg="#ffff00")
        self.d_max.grid(row=1, column=4, padx=2)

        ttk.Button(self.editor_frame, text="💾 SAVE SPLINK CHANGES", command=self.save_splink_editor).pack(fill=tk.X, pady=10)

        # --- BOTTOM: List ---
        list_container = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(list_container, weight=1)

        list_frame = tk.LabelFrame(list_container, text="Active Splinks", bg="#2b2b2b", fg="#888888")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        cols = ("Label", "Source", "Destination", "Mode", "Active")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="w")
        self.tree.column("Source", width=150)
        self.tree.column("Destination", width=150)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_splink)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        controls_frame = tk.Frame(list_container, bg="#2b2b2b", pady=5)
        controls_frame.pack(fill=tk.X)
        ttk.Button(controls_frame, text="New Splink", command=self.create_new_splink).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="🔄 Refresh Splinks", command=self.trigger_refresh).pack(side=tk.LEFT, padx=5)
        
        # --- PANIC CONTROLS ---
        self.panic_btn = tk.Button(controls_frame, text="🆘 PANIC", command=self.trigger_panic, 
                                   bg="#880000", fg="white", font=("Helvetica", 10, "bold"), padx=10)
        self.panic_btn.pack(side=tk.LEFT, padx=20)
        
        self.reset_btn = tk.Button(controls_frame, text="✅ RESET PANIC", command=self.trigger_reset_panic,
                                    bg="#006600", fg="white", font=("Helvetica", 10, "bold"), padx=10)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        self.reset_btn.pack_forget() # Hidden by default
        
        ttk.Button(controls_frame, text="Delete", command=self.delete_selected_splink).pack(side=tk.RIGHT, padx=5)

    def handle_splinker_status(self, payload):
        try:
            data = orjson.loads(payload)
            splinks = data.get("val", data) if isinstance(data, dict) else data
            if isinstance(splinks, list):
                self.splinker_manager.splinks = splinks
                self.refresh_splink_list()
        except Exception as e:
            logger.debug(f"Failed to handle splinker status: {e}")

    def handle_panic_status(self, payload):
        try:
            data = orjson.loads(payload)
            is_panic = data.get("val", False)
            if is_panic:
                self.panic_btn.config(text="🆘 PANIC ACTIVE!", bg="#ff0000", state=tk.DISABLED)
                self.reset_btn.pack(side=tk.LEFT, padx=5, after=self.panic_btn)
                self.refresh_splink_list() # Show deactivated splinks
            else:
                self.panic_btn.config(text="🆘 PANIC", bg="#880000", state=tk.NORMAL)
                self.reset_btn.pack_forget()
        except Exception as e:
            logger.debug(f"Failed to handle panic status: {e}")

    def trigger_panic(self):
        if self.router: self.router.ingest("GUI", "OPEN-AIR/System/Control/Splinker/Panic", "")

    def trigger_reset_panic(self):
        if self.router: self.router.ingest("GUI", "OPEN-AIR/System/Control/Splinker/ResetPanic", "")

    def refresh_splink_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for splink in self.splinker_manager.splinks:
            self.tree.insert("", "end", iid=splink["id"], values=(
                splink.get("label", "N/A"), splink.get("source", "Not Set"),
                splink.get("dest", "Not Set"), splink.get("mode", "BOTH"),
                "Yes" if splink.get("active", False) else "No"
            ))

    def on_select_splink(self, event):
        selected = self.tree.selection()
        if not selected: return
        self.selected_splink_id = selected[0]
        
        splink = next((s for s in self.splinker_manager.splinks if s["id"] == self.selected_splink_id), None)
        if splink:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, splink.get("source", "") or "")
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, splink.get("dest", "") or "")
            self.mode_var.set(splink.get("mode", "BOTH"))
            
            self.s_min.delete(0, tk.END); self.s_max.delete(0, tk.END)
            self.d_min.delete(0, tk.END); self.d_max.delete(0, tk.END)
            
            for h in splink.get("handlers", []):
                if h["type"] == "scale":
                    p = h.get("params", {})
                    self.s_min.insert(0, str(p.get("source_min", 0)))
                    self.s_max.insert(0, str(p.get("source_max", 127)))
                    self.d_min.insert(0, str(p.get("dest_min", 0)))
                    self.d_max.insert(0, str(p.get("dest_max", 100)))

    def save_splink_editor(self):
        if not self.selected_splink_id or not self.router: return
        splink = next((s for s in self.splinker_manager.splinks if s["id"] == self.selected_splink_id), None)
        if not splink: return
        splink["source"] = self.src_entry.get()
        splink["dest"] = self.dest_entry.get()
        splink["mode"] = self.mode_var.get()
        scale_h = next((h for h in splink.get("handlers", []) if h["type"] == "scale"), None)
        if not scale_h:
            scale_h = {"type": "scale", "enabled": True, "params": {}}
            if "handlers" not in splink: splink["handlers"] = []
            splink["handlers"].append(scale_h)
        try:
            scale_h["params"]["source_min"] = float(self.s_min.get() or 0)
            scale_h["params"]["source_max"] = float(self.s_max.get() or 127)
            scale_h["params"]["dest_min"] = float(self.d_min.get() or 0)
            scale_h["params"]["dest_max"] = float(self.d_max.get() or 100)
        except Exception as e:
            logger.error(f"Invalid scaling parameters: {e}")
            messagebox.showerror("Error", f"Invalid scaling parameters: {e}")
            return
        self.router.ingest("GUI", f"OPEN-AIR/System/Control/Splinker/{self.selected_splink_id}/Update", splink)

    def create_new_splink(self):
        if self.router: self.router.ingest("GUI", "OPEN-AIR/System/Control/Splinker/Create", "")

    def trigger_refresh(self):
        if self.router: self.router.ingest("GUI", "OPEN-AIR/System/Control/Splinker/Refresh", "")

    def delete_selected_splink(self):
        if not self.selected_splink_id or not self.router: return
        if messagebox.askyesno("Confirm Delete", f"Delete {self.selected_splink_id}?"):
            self.router.ingest("GUI", f"OPEN-AIR/System/Control/Splinker/{self.selected_splink_id}/Delete", "")

    def destroy(self):
        if self.mqtt_manager:
            self.mqtt_manager.unsubscribe("OPEN-AIR/System/Status/Splinker/List", self.handle_splinker_status)
            self.mqtt_manager.unsubscribe("OPEN-AIR/System/Status/Splinker/Panic", self.handle_panic_status)
        super().destroy()

def get_gui_class():
    return SplinkerEditor
