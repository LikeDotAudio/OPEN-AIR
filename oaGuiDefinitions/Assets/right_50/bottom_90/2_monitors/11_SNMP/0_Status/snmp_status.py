# 0_Status/snmp_status.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
import datetime
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

class SnmpStatus(tk.Frame, TransparencyMixin):
    """
    Combined SNMP Status & Installer Interface.
    Provides live bridge diagnostics and automated setup tools.
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        self.snmp_manager = self._find_snmp_manager(parent)
        
        self._flash_state = False
        self._is_offline = False
        
        self._setup_ui()
        
        if self.snmp_manager:
            self._refresh_ui()
            self._start_monitor_loop()

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
        self.configure(bg="#2b2b2b")

        # 1. Header
        header = tk.Frame(self, bg="#2b2b2b")
        header.pack(side=tk.TOP, fill=tk.X, pady=10)
        tk.Label(header, text="🌐 SNMP BRIDGE STATUS & SETUP", font=("Helvetica", 14, "bold"), fg="#ffffff", bg="#2b2b2b").pack(side=tk.LEFT, padx=20)
        
        self.re_setup_btn = tk.Button(
            header, 
            text="⚠️ RE-SETUP BRIDGE", 
            command=self.refresh_script,
            font=("Helvetica", 10, "bold"),
            bg="#2b2b2b",
            fg="#888888",
            padx=15,
            bd=1,
            relief="raised"
        )
        self.re_setup_btn.pack(side=tk.RIGHT, padx=20)

        # 2. Split View (Status + Installer)
        self.paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- TOP: Bridge Diagnostics ---
        diag_frame = tk.Frame(self.paned, bg="#2b2b2b")
        self.paned.add(diag_frame, weight=1)

        self.tree = ttk.Treeview(diag_frame, columns=("Value"), show="tree", height=6)
        self.tree.heading("#0", text="Property")
        self.tree.column("#0", width=250)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- BOTTOM: Installer Tool ---
        install_frame = tk.LabelFrame(self.paned, text="Linux SNMP Installer Script (Automated Setup)", bg="#2b2b2b", fg="#888888")
        self.paned.add(install_frame, weight=2)

        # Tool buttons
        tool_bar = tk.Frame(install_frame, bg="#2b2b2b")
        tool_bar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        ttk.Button(tool_bar, text="Generate Script", command=self.refresh_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(tool_bar, text="Copy to Clipboard", command=self.copy_script).pack(side=tk.LEFT, padx=5)
        tk.Label(tool_bar, text="Paste this into your Linux Terminal", font=("Courier", 9), fg="#666666", bg="#2b2b2b").pack(side=tk.RIGHT, padx=10)

        # Script area
        self.text_area = tk.Text(install_frame, bg="#000000", fg="#00ff00", font=("Courier", 10), padx=10, pady=10, bd=0)
        scroll = ttk.Scrollbar(install_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scroll.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _start_monitor_loop(self):
        """Periodic background checks for bridge health."""
        self._refresh_ui()
        self._flash_button()
        self.after(5000, self._start_monitor_loop)

    def _flash_button(self):
        """Logic for highlighting the setup button if something is wrong."""
        if self._is_offline:
            self._flash_state = not self._flash_state
            color = "#FFFF00" if self._flash_state else "#2b2b2b"
            text_color = "#000000" if self._flash_state else "#888888"
            self.re_setup_btn.configure(bg=color, fg=text_color)
        else:
            self.re_setup_btn.configure(bg="#2b2b2b", fg="#888888")

    def _refresh_ui(self):
        """Update diagnostics from the SNMP Manager worker."""
        if not self.snmp_manager: return
        
        status = self.snmp_manager.get_status()
        
        # ⚡ HEALTH CHECK
        self._is_offline = not status["running"] or not status["bridge_mode"] or status["object_count"] == 0
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.tree.insert("", "end", text="Bridge Status", values=("ACTIVE" if status["running"] else "OFFLINE",))
        self.tree.insert("", "end", text="Socket Address", values=(status["socket"],))
        self.tree.insert("", "end", text="Root OID", values=(status["base_oid"],))
        self.tree.insert("", "end", text="Variables Active", values=(status["object_count"],))
        self.tree.insert("", "end", text="Operating Mode", values=("MASTER HUB" if status["bridge_mode"] else "OBSERVER ONLY",))
        self.tree.insert("", "end", text="Active MIB", values=(status["mib_path"],))

    def refresh_script(self):
        if not self.snmp_manager: return
        script = self.snmp_manager.get_installer_script()
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", script)
        # Scroll to top
        self.text_area.see("1.0")

    def copy_script(self):
        content = self.text_area.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)

    def render(self):
        self.configure(bg=self.cget("bg"))

def get_gui_class():
    return SnmpStatus
