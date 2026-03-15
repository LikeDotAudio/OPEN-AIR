import math
import tkinter as tk
from workers.styling.style import THEMES, DEFAULT_THEME
from .horizontal_fader_asset_generator import HorizontalFaderAssetGenerator

class HorizontalFaderRendererMixin:
    """Handles the rendering logic for the horizontal linear fader."""

    def render(self):
        if not self.winfo_exists(): return
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        
        for item in self.canvas.find_all():
            if "panel_bg_slice" not in self.canvas.gettags(item): self.canvas.delete(item)
        
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
        
        cy, accent = h/2.0, THEMES.get(DEFAULT_THEME, THEMES["dark"]).get("accent", "#f4902c")
        
        lbl = self.config_data.get("label_active")
        if lbl:
            fs = int(float(self.config_data.get("layout", {}).get("font", 9)))
            self.canvas.create_text(w/2.0, cy-22, text=lbl, fill="white", font=("Arial", fs, "bold"), anchor="s", tags="static")
        
        scale = float(self.config_data.get("fader_cap_scale", 1.0))
        cap_w, cap_h = int(float(self.config_data.get("cap_width", 50))*scale), int(float(self.config_data.get("cap_height", 55))*scale)
        px = cap_w/2.0 + 10.0
        
        self.canvas.create_rectangle(px-5, cy-4, w-px+5, cy+4, fill="#050505", outline="#222", width=1, tags=("static", "track_slot"))
        self.canvas.create_line(px, cy, w-px, cy, fill="#222", width=2, tags="static")
        self.canvas.create_line(px, cy, px, cy, fill=self.config_data.get("value_highlight_color", accent), width=2, tags="fill_line")
        
        self._draw_ticks(w, h, cy, px)
        
        self.cap_img = HorizontalFaderAssetGenerator.get_3d_cap(cap_w, cap_h, self.config_data.get("cap_color", "#dcdcdc"), "#111", highlight_color=self.config_data.get("cap_highlight_color"))
        self.canvas.create_image(px, cy, image=self.cap_img, tags="fader_cap")
        self.canvas.cap_img = self.cap_img
        self.canvas.create_text(px, cy-25, text="", fill="white", font=("Arial", 7, "bold"), tags="floating_val", state="hidden")
        self._update_positions()

    def _draw_ticks(self, w, h, cy, px):
        vr = self.max_val - self.min_val
        ti = self.config_data.get("tick_interval")
        if ti is None:
            if vr > 0:
                e = math.floor(math.log10(vr/10.0)); f = (vr/10.0)/(10**e)
                s = 1 if f < 1.5 else (2 if f < 3.5 else (5 if f < 7.5 else 10))
                ti = s * (10**e)
            else: ti = 10
        
        tv = []
        if float(ti) > 0:
            curr = math.ceil(self.min_val/float(ti))*float(ti)
            while curr <= self.max_val: tv.append(curr); curr += float(ti)
        
        num = len(tv)
        le = 500 if num>5000 else (200 if num>1000 else (50 if num>500 else (20 if num>250 else (10 if num>100 else (5 if num>50 else (2 if num>20 else 1))))))
        de = 100 if le>=500 else (50 if le>=200 else (10 if le>=50 else (5 if le>=20 else (2 if le>=10 else 1))))
        
        uw = w - (px*2.0); tc, stc = self.config_data.get("tick_color", "light grey"), self.config_data.get("sub_tick_color", "#555")
        for i, val in enumerate(tv):
            norm = (val - self.min_val)/vr if vr else 0
            tx = (uw * (max(0.0, min(1.0, norm))**(1.0/self.log_exponent))) + px
            if i % de == 0: self.canvas.create_line(tx, cy+8, tx, cy+14, fill=tc if i%le==0 else stc, tags="static")
            if i % le == 0: self.canvas.create_text(tx, cy+20, text=f"{val:.1f}" if val!=int(val) else str(int(val)), fill=tc, font=("Arial", 7), anchor="n", tags="static")

    def _update_positions(self, *args):
        if not self.winfo_exists() or not self.canvas.winfo_exists(): return
        try: val = self.variable.get()
        except: return
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        scale = float(self.config_data.get("fader_cap_scale", 1.0))
        px = (int(float(self.config_data.get("cap_width", 50))*scale))/2.0 + 10.0
        norm = (val - self.min_val)/(self.max_val-self.min_val) if (self.max_val-self.min_val) else 0
        hx = (w - (px*2.0)) * (max(0.0, min(1.0, norm))**(1.0/self.log_exponent)) + px
        self.canvas.coords("fader_cap", hx, h/2.0); self.canvas.coords("fill_line", px, h/2.0, hx, h/2.0)
        if getattr(self, 'is_sliding', False):
            txt = f"{val:.1f}" if val!=int(val) else str(int(val))
            self.canvas.itemconfig("floating_val", text=txt, state="normal"); self.canvas.coords("floating_val", hx, h/2.0-25.0)
        else: self.canvas.itemconfig("floating_val", state="hidden")
