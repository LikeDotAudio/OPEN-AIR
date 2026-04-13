# renderers/tk_canvas_renderer.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

class TkCanvasRenderer:
    """Specialized renderer for drawing SmartMeter elements onto a Tkinter Canvas."""
    
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.ids = {}

    def clear(self):
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                self.canvas.delete(item)
        self.ids = {}

    def draw_static(self, layout, configuration):
        """Draws the static portions of the meter (track, ticks, grid, labels)."""
        self.clear()
        
        # 0. Industrial Background (Fallback if slice doesn't exist)
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

        width = int(self.canvas.cget("width"))
        height = int(self.canvas.cget("height"))

        # 0.1 Main Widget Label (Floating)
        if configuration.label and configuration.show_label:
            lx, ly, l_anchor = width/2, 10, "n"
            if configuration.label_position == "bottom": ly, l_anchor = height - 10, "s"
            elif configuration.label_position == "left": lx, ly, l_anchor = 5, height/2, "w"
            elif configuration.label_position == "right": lx, ly, l_anchor = width - 5, height/2, "e"
            
            self.canvas.create_text(
                lx, ly, text=configuration.label, fill=configuration.label_colour,
                font=("Helvetica", 10, "bold"), anchor=l_anchor, tags="industrial_text"
            )

        # 1. Bar Track
        self._create_shape('bg', layout.bar_track, fill=configuration.bar_track_bg, outline="")
        
        # 2. Zones (initial draw)
        self.ids['z1'] = self._create_shape('z1', layout.zone1, fill=configuration.lower_colour, outline="")
        self.ids['z2'] = self._create_shape('z2', layout.zone2, fill=configuration.middle_colour, outline="")
        self.ids['z3'] = self._create_shape('z3', layout.zone3, fill=configuration.upper_colour, outline="")
        
        # 3. Grid Lines (Drawn behind ticks but above zones)
        for x1, y1, x2, y2, is_sub in layout.grid_lines:
            self.canvas.create_line(x1, y1, x2, y2, fill=configuration.grid_colour, width=1, tags="grid")
            
        # 4. Ticks
        for x1, y1, x2, y2, is_sub in layout.ticks:
            color = configuration.sub_tick_colour if is_sub else configuration.tick_colour
            width = 1 if is_sub else 2
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            
        # 5. Scale Labels
        for x, y, text, anchor in layout.scale_labels:
            self.canvas.create_text(x, y, text=text, fill=configuration.scale_text_colour, 
                                    font=("Helvetica", configuration.font_size), anchor=anchor)
            
        # 6. Dynamic Element Placeholders
        self.ids['indicator'] = self._create_shape('indicator', layout.indicator, fill=configuration.pointer_colour, outline="")
        
        if configuration.peak_display:
            # We draw peak as a line or rect based on style
            # For "line", get_poly with 0 width returns a collapsed poly. 
            # In update, we'll handle the actual coordinate mapping.
            self.ids['peak'] = self._create_shape('peak', [0,0,0,0], fill=configuration.peak_display_colour, outline="")
            if configuration.peak_flag:
                self.ids['peak_flag'] = self.canvas.create_polygon(0,0,0,0,0,0, fill=configuration.peak_display_colour, outline="")
                
        if configuration.show_peak_hold:
            self.ids['peak_led'] = self.canvas.create_rectangle(*layout.peak_led, fill="#444444", outline="black")

        if self.canvas.find_withtag("grid"):
            self.canvas.tag_raise("grid")

    def update_dynamic(self, dyn_data, overload_factor, configuration):
        """Updates positions and colors of moving elements."""
        
        # Check if grid exists once for optimization
        has_grid = bool(self.canvas.find_withtag("grid"))

        # 1. Update Zone Fills
        for zone in ['z1', 'z2', 'z3']:
            if zone in self.ids:
                self.canvas.coords(self.ids[zone], *dyn_data[zone])
                # ⚡ OPTIMIZATION: Only push below grid if not already done
                if has_grid and not getattr(self, '_z_settled', False):
                    self.canvas.tag_lower(self.ids[zone], "grid")

        self._z_settled = True
                
        # 2. Update Indicator
        if 'indicator' in self.ids:
            self.canvas.coords(self.ids['indicator'], *dyn_data['indicator'])
            
        # 3. Update Peak visuals
        if 'peak' in self.ids:
            # Simple poly update
            self.canvas.coords(self.ids['peak'], *dyn_data['peak'])
            
        if 'peak_flag' in self.ids and dyn_data.get('peak_flag'):
            self.canvas.coords(self.ids['peak_flag'], *dyn_data['peak_flag'])
            
        # 4. Update Overload LED color (Fade)
        if 'peak_led' in self.ids:
            if overload_factor >= 1.0:
                self.canvas.itemconfig(self.ids['peak_led'], fill=configuration.peak_display_colour)
            elif overload_factor <= 0.0:
                self.canvas.itemconfig(self.ids['peak_led'], fill="#444444")
            else:
                fade_color = self._interpolate_color(configuration.peak_display_colour, "#444444", 1.0 - overload_factor)
                self.canvas.itemconfig(self.ids['peak_led'], fill=fade_color)

    def _create_shape(self, tag, coords, **kwargs):
        if len(coords) == 4:
            return self.canvas.create_rectangle(*coords, **kwargs)
        else:
            return self.canvas.create_polygon(*coords, **kwargs)

    def _interpolate_color(self, color1, color2, factor):
        """factor 0.0 = color1, 1.0 = color2"""
        try:
            c1 = self.canvas.winfo_rgb(color1)
            c2 = self.canvas.winfo_rgb(color2)
            r = int(c1[0] + (c2[0] - c1[0]) * factor)
            g = int(c1[1] + (c2[1] - c1[1]) * factor)
            b = int(c1[2] + (c2[2] - c1[2]) * factor)
            return f"#{r>>8:02x}{g>>8:02x}{b>>8:02x}"
        except:
            return color2