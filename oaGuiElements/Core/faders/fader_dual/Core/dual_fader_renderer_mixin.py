import tkinter as tk
from oaGuiElements.Core.faders.fader_dual.Core.dual_fader_asset_generator import DualFaderAssetGenerator

class DualFaderRendererMixin:
    """Handles static background drawing and dynamic handle updates for the Dual Fader."""

    def _draw_fader(self):
        """Redraws the static and background elements."""
        self._resize_timer = None
        if not self.winfo_exists(): return
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        
        # Preserve industrial background slice
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                self.canvas.delete(item)
        
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
        is_vert = self.orientation == "vertical"
        cx, cy = w / 2.0, h / 2.0
        
        if self.label_active: 
            self.canvas.create_text(w / 2.0, 10, text=self.label_active, fill="white", font=("Helvetica", 9, "bold"), tags="static")
            
        if is_vert: 
            self.canvas.create_rectangle(cx - 5, 15, cx + 5, h - 15, fill="#0a0a0a", outline="#333", tags="static")
        else: 
            self.canvas.create_rectangle(15, cy - 5, w - 15, cy + 5, fill="#0a0a0a", outline="#333", tags="static")
            
        self.canvas.create_line(0, 0, 0, 0, fill=self.value_highlight_color, width=4, capstyle=tk.ROUND, tags="delta_line")
        
        cw = self.cap_width
        ch = int((h if not is_vert else w) * self.cap_height_ratio)
        
        # Retrieve or generate the cap image
        self.img1 = DualFaderAssetGenerator.get_3d_dual_fader_cap(ch if is_vert else cw, cw if is_vert else ch, self.cap_color, "#444", is_vert)
        self.img2 = DualFaderAssetGenerator.get_3d_dual_fader_cap(ch if is_vert else cw, cw if is_vert else ch, self.cap_color, "#444", is_vert)
        
        self.canvas.create_image(0, 0, image=self.img1, tags="cap1")
        self.canvas.create_image(0, 0, image=self.img2, tags="cap2")
        self.canvas.create_text(0, 0, text="", fill="white", font=("Helvetica", 7), tags="v1_text")
        self.canvas.create_text(0, 0, text="", fill="white", font=("Helvetica", 7), tags="v2_text")
        self.canvas.create_text(w - 5, h - 5, text="", fill="white", font=("Helvetica", 8, "bold"), anchor="se", tags="delta_label")
        
        self._sync_positions()

    def _sync_positions(self, *args):
        """Updates the dynamic element positions based on value traces."""
        if not self.winfo_exists() or not self.canvas.winfo_exists(): return
        try: 
            v1, v2 = self.v1_var.get(), self.v2_var.get()
            self.delta_var.set(v2 - v1)
        except: return
        
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        is_vert = self.orientation == "vertical"
        dim = h if is_vert else w
        
        def get_p(val):
            n = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            dn = max(0.0, min(1.0, n)) ** (1.0 / self.log_exponent)
            return (dim - 40.0) * (1.0 - dn if is_vert else dn) + 20.0
            
        p1, p2 = get_p(v1), get_p(v2)
        cx, cy = w / 2.0, h / 2.0
        
        if is_vert:
            self.canvas.coords("delta_line", cx, p1, cx, p2)
            self.canvas.coords("cap1", cx, p1)
            self.canvas.coords("cap2", cx, p2)
            self.canvas.coords("v1_text", cx - 25, p1)
            self.canvas.coords("v2_text", cx + 25, p2)
        else:
            self.canvas.coords("delta_line", p1, cy, p2, cy)
            self.canvas.coords("cap1", p1, cy)
            self.canvas.coords("cap2", p2, cy)
            self.canvas.coords("v1_text", p1, cy - 25)
            self.canvas.coords("v2_text", p2, cy + 25)
            
        self.canvas.itemconfig("v1_text", text=f"{v1:.1f}")
        self.canvas.itemconfig("v2_text", text=f"{v2:.1f}")
        self.canvas.itemconfig("delta_label", text=f"\u0394: {v2-v1:.2f}")
