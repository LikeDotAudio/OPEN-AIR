# oaComBroker/Interface/protocol_matrix.py
# Author: Anthony Peter Kuzub
# Version: 20260406.2020.1
#
# Description: Modular N x N Protocol Routing Matrix.
# Allows granular control of "Anything to Anything" routing paths.

import tkinter as tk
from tkinter import ttk

from oaComBroker.Core.protocol_router.manager import ProtocolRouter
from oaLogging.Methods.matrix_gate import matrix_log


class ProtocolMatrix(tk.Frame):
    """
    Modular N x N Matrix of checkboxes to enable/disable specific routing paths.
    Rows = Source (FROM)
    Cols = Destination (TO)
    """
    def __init__(self, parent, **kwargs):
        # Extract non-Tkinter arguments often passed by the LoaderFacade
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
        tk.Label(container, text=r"FROM \ TO", font=("Helvetica", 8, "italic"), fg="#888888", bg="#1a1a1a").grid(row=0, column=0, padx=5, pady=5)

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

        # ⚡ HUB-AND-SPOKE: 2-Column Enablement List
        tk.Label(container, text="INGEST ENABLED", font=("Helvetica", 8, "bold"), fg="#ffff00", bg="#333333", width=20).grid(row=0, column=1, padx=5, pady=5)
        tk.Label(container, text="EGRESS ENABLED", font=("Helvetica", 8, "bold"), fg="#ffff00", bg="#333333", width=20).grid(row=0, column=2, padx=5, pady=5)

        self.ingest_vars = {}
        self.egress_vars = {}

        for r, proto in enumerate(protocols):
            # Row Header
            emoji = self.router.protocol_emojis.get(proto, "")
            lbl = tk.Label(container, text=f"{proto} {emoji}", font=("Courier", 8, "bold"), fg="#00ff00", bg="#1a1a1a", width=15, anchor="e")
            lbl.grid(row=r+1, column=0, padx=10, pady=2)

            # Ingest Toggle
            ingest_var = tk.BooleanVar(value=self.router.ingest_enabled.get(proto, True))
            cb_ingest = tk.Checkbutton(container, variable=ingest_var, bg="#1a1a1a", selectcolor="#000000",
                                       command=lambda p=proto, v=ingest_var: self._on_toggle_ingest(p, v))
            cb_ingest.grid(row=r+1, column=1, padx=2, pady=2)
            self.ingest_vars[proto] = ingest_var

            # Egress Toggle
            egress_var = tk.BooleanVar(value=self.router.egress_enabled.get(proto, True))
            cb_egress = tk.Checkbutton(container, variable=egress_var, bg="#1a1a1a", selectcolor="#000000",
                                       command=lambda p=proto, v=egress_var: self._on_toggle_egress(p, v))
            cb_egress.grid(row=r+1, column=2, padx=2, pady=2)
            self.egress_vars[proto] = egress_var

    def _on_toggle_ingest(self, proto, var):
        enabled = var.get()
        self.router.ingest_enabled[proto] = enabled
        self.router._save_routing_config(proto, "ingest", enabled)
        matrix_log("comms", "broker", "ui_ingress", f"🔄 [ROUTING] {proto} Ingest: {enabled}", "INFO")

    def _on_toggle_egress(self, proto, var):
        enabled = var.get()
        self.router.egress_enabled[proto] = enabled
        self.router._save_routing_config(proto, "egress", enabled)
        matrix_log("comms", "broker", "ui_egress", f"🔄 [ROUTING] {proto} Egress: {enabled}", "INFO")
def get_gui_class():
    return ProtocolMatrix
