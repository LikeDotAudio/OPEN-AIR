# oaGui/Managers/interaction_view_states.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Manages visibility groups and right-click toggle menus for collapsible sections.

import tkinter as tk


class InteractionViewStates:
    """Manages visibility groups and right-click toggle menus for collapsible sections."""
    def __init__(self, root_widget: tk.Widget, builder=None):
        self.groups = {}
        self.vars = {}
        self.builder = builder
        self.menu = tk.Menu(root_widget, tearoff=0)

        # If we are in the builder, add those standard items
        if self.builder and hasattr(self.builder, "populate_context_menu"):
            self.builder.populate_context_menu(self.menu)
            self.menu.add_separator()

    def register(self, group_name: str, widget: tk.Widget):
        """Registers a widget into a visibility group."""
        if group_name not in self.groups:
            self._initialize_group(group_name)
        self.groups[group_name].append(widget)

    def _initialize_group(self, group_name: str):
        self.groups[group_name] = []
        var = tk.BooleanVar(value=True)
        self.vars[group_name] = var
        self.menu.add_checkbutton(
            label=f"Show {group_name}",
            variable=var,
            command=lambda g=group_name: self._toggle_group(g)
        )

    def _toggle_group(self, group_name: str):
        is_visible = self.vars[group_name].get()
        state = "expanded" if is_visible else "collapsed"
        for widget in self.groups.get(group_name, []):
            if hasattr(widget, "set_view_state"):
                widget.set_view_state(state)

    def show_menu(self, event):
        """Displays the visibility toggle menu."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
