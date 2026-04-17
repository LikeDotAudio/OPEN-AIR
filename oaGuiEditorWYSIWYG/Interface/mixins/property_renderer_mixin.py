# Interface/mixins/property_renderer_mixin.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Handles the recursive generation of the properties UI tree.

from ...Core.state import state_manager
from ..renderers.tree_renderer import TreeRenderer

class PropertyRendererMixin:
    """Handles the recursive generation of the properties UI tree."""

    def __init__(self):
        super().__init__()
        self.widget_cache = {} # Cache to store rendered widgets by path

    def _render_recursive_properties(self, data, parent, prefix="", depth=0, actual_data=None, widget_cache=None, new_widget_cache=None):
        """Delegates rendering to the modular TreeRenderer."""
        TreeRenderer.render_recursive(
            data, parent, prefix, depth, actual_data, 
            widget_cache, new_widget_cache, mixin_ref=self
        )

    def _add_state_item(self, path, value):
        """State manipulation logic (Logic stayed in mixin)."""
        state_manager.update_state(value, path=path, source=self)
        if hasattr(self, '_refresh_content'):
            self._refresh_content()

    def _reorder(self, path, direction):
        """Structural logic (Logic stayed in mixin)."""
        state_manager.reorder_element(path, direction, source=self)
