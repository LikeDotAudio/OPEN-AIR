# Interface/mixins/layout_tools_mixin.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Quick Alignment and Sticky UI tools for the properties panel.

from ...Core.state import state_manager
from ..renderers.alignment_renderer import AlignmentRenderer
from ..renderers.sticky_renderer import StickyRenderer

class LayoutToolsMixin:
    """Provides Quick Alignment and Sticky UI tools for the properties panel."""

    def _render_alignment_quick_tools(self, data, container):
        layout = data.get("layout", {})
        align = str(layout.get("align", "")).lower()
        self._align_buttons = AlignmentRenderer.render(container, align, self._set_align)

    def _render_sticky_quick_tools(self, data, container):
        layout = data.get("layout", {})
        stretch = str(layout.get("stretch", "")).lower()
        self._sticky_buttons = StickyRenderer.render(container, stretch, self._set_sticky_preset)

    def _set_align(self, mode):
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
        
        AlignmentRenderer.update_highlights(self._align_buttons, new_align)
        StickyRenderer.update_highlights(self._sticky_buttons, new_stretch)
        self._request_debounced_refresh()

    def _set_sticky_preset(self, mode):
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
        
        AlignmentRenderer.update_highlights(self._align_buttons, new_align)
        StickyRenderer.update_highlights(self._sticky_buttons, new_stretch)
        self._request_debounced_refresh()
