import tkinter as tk
from ...core.state import state_manager

class LayoutToolsMixin:
    """Provides Quick Alignment and Sticky UI tools for the properties panel."""

    def _render_alignment_quick_tools(self, data, container):
        tk.Label(container, text="QUICK ALIGNMENT (ANCHOR)", bg="#252525", fg="#888888", font=("Arial", 7, "bold")).pack()
        btn_frame = tk.Frame(container, bg="#252525")
        btn_frame.pack(pady=(5, 10))

        layout = data.get("layout", {})
        align = str(layout.get("align", "")).lower()
        buttons = {}

        def set_align(mode):
            current_data = state_manager.get_value_at_path(self.focused_path)
            curr_layout = current_data.get("layout", {})
            curr_align = set(str(curr_layout.get("align", "")).lower().split())
            curr_stretch = set(str(curr_layout.get("stretch", "")).lower().split())
            
            if mode == "L":
                if "left" in curr_align: curr_align.discard("left")
                else: curr_align.discard("right"); curr_align.add("left"); curr_stretch.discard("width"); curr_stretch.discard("both")
            elif mode == "R":
                if "right" in curr_align: curr_align.discard("right")
                else: curr_align.discard("left"); curr_align.add("right"); curr_stretch.discard("width"); curr_stretch.discard("both")
            elif mode == "T":
                if "top" in curr_align: curr_align.discard("top")
                else: curr_align.discard("bottom"); curr_align.add("top"); curr_stretch.discard("height"); curr_stretch.discard("both")
            elif mode == "B":
                if "bottom" in curr_align: curr_align.discard("bottom")
                else: curr_align.discard("top"); curr_align.add("bottom"); curr_stretch.discard("height"); curr_stretch.discard("both")
            elif mode == "C": curr_align.clear()

            new_align = " ".join(sorted(list(curr_align)))
            new_stretch = " ".join(sorted(list(curr_stretch)))
            state_manager.update_state({"align": new_align, "stretch": new_stretch}, path=f"{self.focused_path}.layout", source=self)
            self._update_tool_highlights(new_align, new_stretch, buttons, self._sticky_buttons)
            self._request_debounced_refresh()

        for label in ["L", "R", "T", "B", "C"]:
            active = (label == "L" and "left" in align) or (label == "R" and "right" in align) or \
                     (label == "T" and "top" in align) or (label == "B" and "bottom" in align) or \
                     (label == "C" and not align)
            btn = tk.Button(btn_frame, text=label, width=3, bg="#33A1FD" if active else "#444444", fg="white", 
                            relief="flat", font=("Arial", 8, "bold"), command=lambda l=label: set_align(l))
            btn.pack(side="left", padx=2)
            buttons[label] = btn
        self._align_buttons = buttons

    def _render_sticky_quick_tools(self, data, container):
        tk.Label(container, text="QUICK STICKY (STRETCH)", bg="#252525", fg="#888888", font=("Arial", 7, "bold")).pack()
        btn_frame = tk.Frame(container, bg="#252525")
        btn_frame.pack(pady=5)

        layout = data.get("layout", {})
        stretch = str(layout.get("stretch", "")).lower()
        buttons = {}

        def set_sticky_preset(mode):
            current_data = state_manager.get_value_at_path(self.focused_path)
            curr_layout = current_data.get("layout", {})
            curr_align = set(str(curr_layout.get("align", "")).lower().split())
            curr_stretch = set(str(curr_layout.get("stretch", "")).lower().split())
            
            new_mode = mode.lower()
            if new_mode == "width":
                if "width" in curr_stretch: curr_stretch.discard("width")
                elif "both" in curr_stretch: curr_stretch.discard("both"); curr_stretch.add("height")
                else: curr_stretch.add("width"); curr_align.discard("left"); curr_align.discard("right")
            elif new_mode == "height":
                if "height" in curr_stretch: curr_stretch.discard("height")
                elif "both" in curr_stretch: curr_stretch.discard("both"); curr_stretch.add("width")
                else: curr_stretch.add("height"); curr_align.discard("top"); curr_align.discard("bottom")
            elif new_mode == "both":
                if "both" in curr_stretch: curr_stretch.clear()
                else: curr_stretch = {"both"}; curr_align.clear()
            else: curr_stretch.clear()

            new_align = " ".join(sorted(list(curr_align)))
            new_stretch = " ".join(sorted(list(curr_stretch)))
            state_manager.update_state({"align": new_align, "stretch": new_stretch}, path=f"{self.focused_path}.layout", source=self)
            self._update_tool_highlights(new_align, new_stretch, self._align_buttons, buttons)
            self._request_debounced_refresh()

        presets = [("EW", "width"), ("NS", "height"), ("NSEW", "both"), ("NONE", "")]
        for label, val in presets:
            active = (val in stretch) or (label == "NONE" and not stretch)
            btn = tk.Button(btn_frame, text=label, width=5, bg="#2ecc71" if active else "#444444", fg="white", 
                            relief="flat", font=("Arial", 7, "bold"), command=lambda v=val: set_sticky_preset(v))
            btn.pack(side="left", padx=2)
            buttons[label] = btn
        self._sticky_buttons = buttons

    def _update_tool_highlights(self, align_str, stretch_str, align_btns, sticky_buttons):
        a, s = set(align_str.split()), set(stretch_str.split())
        for l, b in align_btns.items():
            active = (l=="L" and "left" in a) or (l=="R" and "right" in a) or (l=="T" and "top" in a) or (l=="B" and "bottom" in a) or (l=="C" and not a)
            b.config(bg="#33A1FD" if active else "#444444")
        for l, b in sticky_buttons.items():
            active = (l=="EW" and ("width" in s or "both" in s)) or (l=="NS" and ("height" in s or "both" in s)) or (l=="NSEW" and "both" in s) or (l=="NONE" and not s)
            b.config(bg="#2ecc71" if active else "#444444")
