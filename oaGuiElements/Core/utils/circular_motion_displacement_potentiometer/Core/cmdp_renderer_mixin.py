# Core/cmdp_renderer_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

class CMDPRendererMixin:
    """Handles canvas-level static UI rendering and resize logic for the CMDP widget."""

    def draw_static_ui(self):
        self.canvas.delete("static_ui")
        cx, cy, n, f = self.center_x, self.center_y, self.near_radius, self.far_radius
        accent = "#f4902c"
        
        # Guides
        self.canvas.create_oval(cx-n, cy-n, cx+n, cy+n, outline=accent, dash=(5,5), width=2, tags="static_ui")
        self.canvas.create_oval(cx-f, cy-f, cx+f, cy+f, outline=accent, dash=(5,5), width=2, tags="static_ui")
        
        # Center Icon (Head)
        r = 40
        self.canvas.create_oval(cx-r-10, cy-15, cx-r+5, cy+15, fill="#444", outline=accent, width=2, tags="static_ui")
        self.canvas.create_oval(cx+r-5, cy-15, cx+r+10, cy+15, fill="#444", outline=accent, width=2, tags="static_ui")
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#444", outline=accent, width=2, tags="static_ui")
        self.canvas.create_polygon(cx, cy-r-15, cx-10, cy-r+5, cx+10, cy-r+5, fill=accent, tags="static_ui")

    def on_canvas_resize(self, event):
        self.center_x, self.center_y = event.width // 2, event.height // 2
        s = min(event.width, event.height)
        self.near_radius, self.far_radius = s * 0.12, s * 0.45
        self.draw_static_ui()
        for f in self.faders: f.update_position_and_render()
