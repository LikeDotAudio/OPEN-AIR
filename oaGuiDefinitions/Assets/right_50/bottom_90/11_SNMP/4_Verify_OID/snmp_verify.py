# 4_Verify_OID/snmp_verify.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

class SnmpVerifyOid(tk.Frame, TransparencyMixin):
    """
    Simplified SNMP Verification Tool.
    Focuses strictly on raw numerical OIDs.
    """
    def __init__(self, parent, json_path=None, config=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.snmp_manager = self._find_snmp_manager(parent)
        self._setup_ui()

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

        lbl = ttk.Label(header_frame, text="Raw OID Verification (Numerical)", font=("Helvetica", 12, "bold"), background=self.cget("bg"))
        lbl.pack(side=tk.LEFT, padx=10)

        self.counter_var = tk.StringVar(value="Topics: 0")
        counter_lbl = ttk.Label(header_frame, textvariable=self.counter_var, font=("Courier", 10, "bold"), foreground="#00ff00", background=self.cget("bg"))
        counter_lbl.pack(side=tk.RIGHT, padx=20)

        # 2. Footer (Buttons)
        btn_frame = tk.Frame(self, bg=self.cget("bg"))
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Run Raw snmpwalk", command=self.run_test).pack(side=tk.LEFT, padx=10)
        
        # Filter Logic
        filter_frame = tk.Frame(btn_frame, bg=self.cget("bg"))
        filter_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(filter_frame, text="Filter Prefix:", background=self.cget("bg")).pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value=".1.3.6.1.4.1.65300.")
        # Use tk.Entry for explicit color control
        self.filter_entry = tk.Entry(filter_frame, textvariable=self.filter_var, width=40, bg="#000000", fg="#888888", insertbackground="white", bd=1, relief="flat")
        self.filter_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Clear Output", command=self.clear).pack(side=tk.LEFT)

        # 3. Mode Status
        self.path_lbl = ttk.Label(self, text="Mode: Strictly Numerical (-On)", background=self.cget("bg"), foreground="#aaa", font=("Courier", 9))
        self.path_lbl.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 5))

        # 4. Content Area
        display_frame = tk.Frame(self, bg=self.cget("bg"))
        display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.text_area = tk.Text(display_frame, bg="#1e1e1e", fg="#FFAA00", font=("Courier", 10), padx=10, pady=10)
        scroll = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scroll.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0))
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,10))

    def run_test(self):
        if not self.snmp_manager: return
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, "Executing raw walk on localhost...\n")
        self.text_area.insert(tk.END, "-"*40 + "\n")
        self.update()
        
        # Calling without a path forces RAW mode in SnmpTester
        output = self.snmp_manager.run_verification()
        
        # Apply Filter
        filter_str = self.filter_var.get()
        if filter_str:
            lines = output.splitlines()
            filtered_lines = [line.replace(filter_str, "") for line in lines]
            output = "\n".join(filtered_lines)

        # Update Counter (Count lines that look like OID assignments)
        count = sum(1 for line in output.splitlines() if " = " in line)
        self.counter_var.set(f"Topics: {count}")

        self.text_area.insert(tk.END, output)

    def clear(self):
        self.text_area.delete("1.0", tk.END)
        self.counter_var.set("Topics: 0")

    def render(self):
        self.configure(bg=self.cget("bg"))
