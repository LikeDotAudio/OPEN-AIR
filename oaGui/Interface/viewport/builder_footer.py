# Interface/builder_footer.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Telemetry footer for the Dynamic GUI Builder.

import tkinter as tk


class BuilderFooter(tk.Frame):
    """Optional telemetry display footer for the Dynamic GUI Builder."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#111111", height=18, **kwargs)
        self.grid_propagate(False)
        self._init_labels()

    def _init_labels(self):
        self.viewport_lbl = tk.Label(self, text="Viewport: 0x0", bg="#111111", fg="#888888", font=("Arial", 7))
        self.viewport_lbl.pack(side="left", padx=10)

        self.content_lbl = tk.Label(self, text="Content: 0x0", bg="#111111", fg="#888888", font=("Arial", 7))
        self.content_lbl.pack(side="left", padx=10)

        self.telemetry_geo_lbl = tk.Label(self, text="GEO: IDLE", bg="#111111", fg="#00FFFF", font=("Arial", 7))
        self.telemetry_geo_lbl.pack(side="right", padx=10)

        self.telemetry_cmd_lbl = tk.Label(self, text="TX: IDLE", bg="#111111", fg="#00FF00", font=("Arial", 7))
        self.telemetry_cmd_lbl.pack(side="right", padx=10)

    def update_dimensions(self, width, height, req_w, req_h):
        """Updates the viewport and content dimension labels with a pulse effect."""
        new_view = f"Viewport: {width}x{height}"
        new_cont = f"Content: {req_w}x{req_h}"

        if self.viewport_lbl.cget("text") != new_view:
            self.viewport_lbl.config(text=new_view, fg="#FFFFFF")
            self.after(300, lambda: self.viewport_lbl.config(fg="#888888") if self.winfo_exists() else None)

        if self.content_lbl.cget("text") != new_cont:
            self.content_lbl.config(text=new_cont, fg="#FFFFFF")
            self.after(300, lambda: self.content_lbl.config(fg="#888888") if self.winfo_exists() else None)

    def log_telemetry_tx(self, message):
        """Logs geometry telemetry transmission."""
        self.telemetry_geo_lbl.config(text=str(message))
        self.telemetry_geo_lbl.config(fg="#FFFFFF")
        self.telemetry_geo_lbl.update_idletasks()
        self.after(200, lambda: self.telemetry_geo_lbl.config(fg="#00FFFF") if self.winfo_exists() else None)

    def log_command_tx(self, message):
        """Logs command telemetry transmission."""
        display_msg = str(message)[:60] + ("..." if len(str(message)) > 60 else "")
        self.telemetry_cmd_lbl.config(text=f"TX: {display_msg}")
        self.telemetry_cmd_lbl.config(fg="#FFFFFF")
        self.telemetry_cmd_lbl.update_idletasks()
        self.after(200, lambda: self.telemetry_cmd_lbl.config(fg="#00FF00") if self.winfo_exists() else None)
