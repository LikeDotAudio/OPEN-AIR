# collapsible_block/collapsible_block.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---

app_constants = Config.get_instance()

from oaGui.Core.context.cache_widget_context import WidgetContext
from oaGui.Workers.compositing.sync_behavior import SyncBehavior


class CollapsibleBlockCreatorMixin(SyncBehavior):
    def _create_collapsible_block(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """
        Creates a frame that can be collapsed into a placeholder.
        Binds right-click to show the global view menu.
        """
        # ⚡ HARDENED INTERFACE: Extract from context if available
        on_complete = context.on_complete if context else kwargs.get("on_complete")
        builder_instance = context.builder_instance if context else kwargs.get("builder_instance") or self

        # 1. Create the wrapper frame (tk.Canvas for transparency)
        p_bg = "#2b2b2b"
        try: p_bg = parent_widget.cget("bg")
        except: pass
        wrapper = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", bg=p_bg)

        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(wrapper, wrapper, config_data, builder_instance)

        # 2. Content Frame (The OcaBlock)
        content_frame = tk.Canvas(wrapper, bd=0, highlightthickness=0, relief="flat")

        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(content_frame, content_frame, config_data, builder_instance)

        # --- GRID CONFIGURATION ---
        max_cols = int(config_data.get("layout_columns", 1))
        column_sizing = config_data.get("column_sizing", [])
        for col_idx in range(max_cols):
            sizing_info = column_sizing[col_idx] if col_idx < len(column_sizing) else {}
            weight = sizing_info.get("weight", 1)
            minwidth = sizing_info.get("minwidth", 0)
            content_frame.grid_columnconfigure(col_idx, weight=weight, minsize=minwidth)

        # 3. Placeholder Frame (Hidden by default)
        placeholder_frame = tk.Canvas(wrapper, height=5, bd=0, highlightthickness=0, relief="flat")
        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(placeholder_frame, placeholder_frame, config_data, self)

        separator = ttk.Separator(placeholder_frame, orient="horizontal")
        separator.pack(fill="x", expand=True, pady=2)

        # 4. Context Menu Binding
        interaction_view_states = config_data.get("_view_manager", None)
        # ⚡ JSON ALIAS: Support 'view' or 'view_group'
        view_group = config_data.get("view", config_data.get("view_group", None))

        if interaction_view_states:
            def show_global_menu(event):
                interaction_view_states.show_menu(event)

            wrapper.bind("<Button-3>", show_global_menu)
            content_frame.bind("<Button-3>", show_global_menu)
            placeholder_frame.bind("<Button-3>", show_global_menu)
            separator.bind("<Button-3>", show_global_menu)

        # 5. Attach State Logic
        def set_view_state(state):
            if state == "expanded":
                placeholder_frame.pack_forget()
                content_frame.pack(fill="both", expand=True)
            elif state == "collapsed":
                content_frame.pack_forget()
                placeholder_frame.pack(fill="x", expand=False)

        wrapper.set_view_state = set_view_state

        if interaction_view_states and view_group:
            interaction_view_states.register(view_group, wrapper)

        set_view_state("expanded")

        # 6. Build Children
        # ⚡ SPEED: Only build if we have fields
        if "fields" in config_data:
            self._create_dynamic_widgets(
                content_frame, config_data,
                path_prefix=config_data.get("path",""),
                on_complete=on_complete,
                context=context
            )
        elif on_complete:
            on_complete()

        return wrapper

