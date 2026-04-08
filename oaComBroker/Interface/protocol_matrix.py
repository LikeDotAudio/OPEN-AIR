# oaComBroker/Interface/protocol_matrix.py
# Author: Anthony Peter Kuzub
# Version: 20260406.2020.1
#
# Description: Modular N x N Protocol Routing Matrix.
# Allows granular control of "Anything to Anything" routing paths.

import tkinter as tk
from tkinter import ttk
import time
from oaLogging.Methods.matrix_gate import matrix_log
from oaComBroker.Core.protocol_router.manager import ProtocolRouter

class ProtocolMatrix(tk.Frame):
    """
    Modular N x N Matrix of checkboxes to enable/disable specific routing paths.
    Rows = Source (FROM)
    Cols = Destination (TO)
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments often passed by the ModuleLoader
        self.config_data = kwargs.pop("config", {})
        self.json_path = kwargs.pop("json_path", None)
        
        super().__init__(parent, **kwargs)
        self.router = ProtocolRouter.get_instance()
        self._setup_ui()

    def _setup_ui(self):
        self.configure(bg="#1a1a1a")
        
        title_label = tk.Label(self, text="🛰️ N x N PROTOCOL ROUTING CROSS-POINT & STRATEGY", font=("Helvetica", 10, "bold"), fg="#ffffff", bg="#333333")
        title_label.pack(fill=tk.X)
        
        # Scrollable container for the large matrix
        canvas = tk.Canvas(self, bg="#1a1a1a", highlightthickness=0)
        scrollbar_v = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        
        self.scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        container = self.scrollable_frame
        
        # Legend/Axis Labels
        tk.Label(container, text="FROM \ TO", font=("Helvetica", 8, "italic"), fg="#888888", bg="#1a1a1a").grid(row=0, column=0, padx=5, pady=5)

        self.matrix_vars = {}
        self.strategy_previews = {}
        
        protocols = self.router.protocols
        
        # 1. Column Headers (Destinations + Emojis)
        for c, dest in enumerate(protocols):
            emoji = self.router.protocol_emojis.get(dest, "")
            header_text = f"{emoji}\n{dest}"
            lbl = tk.Label(container, text=header_text, font=("Courier", 8, "bold"), fg="#ffff00", bg="#1a1a1a", width=12)
            lbl.grid(row=0, column=c+1, padx=2, pady=5)

        # Strategy Header
        tk.Label(container, text="CURRENT STRATEGY", font=("Helvetica", 8, "bold"), fg="#ffffff", bg="#333333", width=20).grid(row=0, column=len(protocols)+1, padx=10)

        # 2. Rows (Sources)
        for r, src in enumerate(protocols):
            # Row Header
            src_emoji = self.router.protocol_emojis.get(src, "")
            lbl = tk.Label(container, text=f"{src} {src_emoji}", font=("Courier", 8, "bold"), fg="#00ff00", bg="#1a1a1a", width=12, anchor="e")
            lbl.grid(row=r+1, column=0, padx=10, pady=2)
            
            for c, dest in enumerate(protocols):
                is_diagonal = (src == dest)
                initial_enabled = self.router.routing_matrix.get(src, {}).get(dest, True)
                
                cell_frame = tk.Frame(container, bg="#1a1a1a", bd=1, relief="flat")
                cell_frame.grid(row=r+1, column=c+1, padx=1, pady=1)
                
                if not is_diagonal:
                    # Enable Checkbox
                    var = tk.BooleanVar(value=initial_enabled)
                    cb = tk.Checkbutton(
                        cell_frame, variable=var, bg="#1a1a1a", selectcolor="#000000",
                        command=lambda s=src, d=dest, v=var: self._on_toggle_route(s, d, v)
                    )
                    cb.pack()
                    
                    self.matrix_vars[(src, dest)] = var
                else:
                    # ✖ Deny the user from selecting self-routing
                    tk.Label(cell_frame, text="✖", font=("Courier", 8), fg="#444444", bg="#1a1a1a").pack()

            # 3. Strategy Preview Column
            preview_var = tk.StringVar(value=self.router.get_strategy_for_source(src))
            lbl_preview = tk.Label(container, textvariable=preview_var, font=("Segoe UI Emoji", 10), fg="#00ffff", bg="#000000", width=20)
            lbl_preview.grid(row=r+1, column=len(protocols)+1, padx=10)
            self.strategy_previews[src] = preview_var

    def _on_toggle_route(self, src, dest, var):
        """Handler for checkbox toggles in the cross-point matrix."""
        enabled = var.get()
        self.router.set_routing_state(src, dest, enabled)
        
        # Update Preview
        self.strategy_previews[src].set(self.router.get_strategy_for_source(src))
        
        # ⚡ FORENSIC TELEMETRY
        self.router.ingest(
            transport_source="SYSTEM", 
            topic=f"OPEN-AIR/System/Router/Route/{src}/{dest}", 
            value="ENABLED" if enabled else "DISABLED",
            metadata={"msg_type": "ROUTING_GATE", "is_settled": True}
        )

def get_gui_class():
    return ProtocolMatrix
