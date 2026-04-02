import os

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# 3_MIB/snmp_mib.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
from loguru import logger
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaOchestration.Constants.project_paths import SNMP_CURRENT_MIB

class SnmpMib(tk.Frame, TransparencyMixin):
    """
    MIB File Generator View.
    Always manages and displays the 'current.mib' file with auto-reload.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.snmp_manager = self._find_snmp_manager(parent)
        self._last_mtime = 0
        self._setup_ui()
        
        # Initial load
        self.load_mib_from_disk()
        # Start background update checker
        self._check_for_disk_updates()

    def _find_snmp_manager(self, widget):
        from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
        curr = widget
        while curr:
            if isinstance(curr, DynamicGuiBuilder) and hasattr(curr, 'app_instance'):
                return getattr(curr.app_instance, 'snmp_manager', None)
            try: curr = curr.master
            except: break
        return None

    def _setup_ui(self):
        self.pack(fill=tk.BOTH, expand=True)
        
        # 1. Header Frame
        header_frame = tk.Frame(self, bg=self.cget("bg"))
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        lbl = ttk.Label(header_frame, text="Persistent MIB Definition (current.mib)", font=("Helvetica", 12, "bold"), background=self.cget("bg"))
        lbl.pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Status: In Sync")
        status_lbl = ttk.Label(header_frame, textvariable=self.status_var, font=("Courier", 9), foreground="#aaa", background=self.cget("bg"))
        status_lbl.pack(side=tk.RIGHT, padx=20)

        # 2. Footer (Buttons at the bottom)
        btn_frame = tk.Frame(self, bg=self.cget("bg"))
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Force Refresh", command=self.refresh_mib).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Save As...", command=self.save_mib_as).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Load External MIB...", command=self.load_mib_dialog).pack(side=tk.LEFT)

        # 3. Content Area
        display_frame = tk.Frame(self, bg=self.cget("bg"))
        display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.text_area = tk.Text(display_frame, bg="#1e1e1e", fg="#33A1FD", font=("Courier", 10), padx=10, pady=10)
        scroll = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scroll.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0))
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,10))

    def _check_for_disk_updates(self):
        """Periodically checks if current.mib was updated by the Core process."""
        if SNMP_CURRENT_MIB.exists():
            try:
                mtime = os.path.getmtime(SNMP_CURRENT_MIB)
                if mtime > self._last_mtime:
                    self.load_mib_from_disk()
                    self._last_mtime = mtime
                    self.status_var.set("Status: Auto-Updated")
            except: pass
        
        if not getattr(self, '_shutdown', False):
            self.after(5000, self._check_for_disk_updates)

    def load_mib_from_disk(self, path=None):
        target = path or SNMP_CURRENT_MIB
        if target.exists():
            try:
                with open(target, "r") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self._last_mtime = os.path.getmtime(target)
            except Exception as e:
                logger.error(f"❌ SNMP UI: Failed to read MIB from disk: {e}")

    def refresh_mib(self):
        """Forces the manager to regenerate the MIB."""
        if not self.snmp_manager: return
        self.status_var.set("Status: Refreshing...")
        if self.snmp_manager.save_current_mib():
            self.load_mib_from_disk()
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "💾 SNMP UI: current.mib refreshed.", "SUCCESS")
            self.status_var.set("Status: Refreshed")

    def save_mib_as(self):
        from tkinter import filedialog
        mib_content = self.text_area.get("1.0", tk.END)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mib",
            filetypes=[("MIB Files", "*.mib"), ("Text Files", "*.txt")],
            initialfile="OPEN-AIR.mib"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(mib_content)
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"💾 SNMP: MIB saved to {file_path}", "SUCCESS")
            except Exception as e:
                logger.error(f"❌ SNMP: Failed to save MIB: {e}")

    def load_mib_dialog(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            filetypes=[("MIB Files", "*.mib"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            from pathlib import Path
            self.load_mib_from_disk(Path(file_path))
            self.status_var.set(f"Status: Loaded {os.path.basename(file_path)}")

    def render(self):
        self.configure(bg=self.cget("bg"))

    def destroy(self):
        self._shutdown = True
        super().destroy()