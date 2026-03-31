# json_tree/json_tree.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized JSON Tree Viewer.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from tkinter import ttk, filedialog
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from oaGuiElements.Core.utils.json_tree.Core.json import JsonDataManager
from oaGuiElements.Core.utils.json_tree.Core.json_tree_renderer_mixin import JsonTreeRendererMixin
from oaGuiElements.Core.utils.json_tree.Core.json_tree_editor_mixin import JsonTreeEditorMixin

class AutoScrollbar(ttk.Scrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0: self.grid_remove()
        else: self.grid()
        ttk.Scrollbar.set(self, lo, hi)

class JsonTreeWidget(
    tk.Frame,
    JsonTreeRendererMixin,
    JsonTreeEditorMixin
):
    """Encapsulated widget for JSON Tree operations."""
    
    def __init__(self, parent, config, state_mirror_engine, base_mqtt_topic):
        super().__init__(parent)
        self.config_data = config
        self.state_mirror_engine = state_mirror_engine
        self.base_mqtt_topic = base_mqtt_topic
        self.data_manager = JsonDataManager()
        
        self.allow_browse = config.get("ALLOW", {}).get("browse", config.get("allow_browse", True))
        self.allow_filter = config.get("ALLOW", {}).get("filter", config.get("allow_filter", True))
        self.allow_edit = config.get("ALLOW", {}).get("edit", config.get("allow_edit", False))
        self.allow_save_as = config.get("ALLOW", {}).get("save_as", False)
        self.allow_expand_all = config.get("ALLOW", {}).get("expand_all", False)
        self.allow_table_toggle = config.get("ALLOW", {}).get("table_toggle", True)
        
        self.show_values_var = tk.BooleanVar(value=config.get("show_values", False))
        self._setup_ui()
        
        if self.allow_edit: self._setup_editing()
        
        source = config.get("json_source")
        if source: self.load_json(source)

    def _setup_ui(self):
        # 1. Header
        self.header = tk.Frame(self)
        self.header.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        label = self.config_data.get("label_active")
        if label and self.config_data.get("show_label", True):
            self.lbl = tk.Label(self.header, text=label, font=("Helvetica", 10, "bold"), fg="white")
            self.lbl.pack(side=tk.LEFT, anchor="w")

        if self.allow_browse:
            ttk.Button(self.header, text="Browse...", command=self.browse_file).pack(side=tk.RIGHT, padx=2)

        # 2. Controls
        if self.allow_filter or self.allow_expand_all or self.allow_table_toggle:
            self.ctrl = tk.Frame(self)
            self.ctrl.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
            
            if self.allow_expand_all:
                ttk.Button(self.ctrl, text="Expand All", command=lambda: self._toggle_all(True)).pack(side=tk.LEFT, padx=2)
                ttk.Button(self.ctrl, text="Collapse All", command=lambda: self._toggle_all(False)).pack(side=tk.LEFT, padx=2)

            if self.allow_table_toggle:
                ttk.Checkbutton(self.ctrl, text="Table View", variable=self.show_values_var, command=self._on_view_toggle).pack(side=tk.LEFT, padx=5)
            
            if self.allow_filter:
                tk.Label(self.ctrl, text="Filter: ", fg="white").pack(side=tk.LEFT)
                self.filter_var = tk.StringVar()
                self.filter_var.trace_add("write", lambda *a: self.refresh_tree_display(self.filter_var.get(), self.show_values_var.get()))
                ttk.Entry(self.ctrl, textvariable=self.filter_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 3. Tree
        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        vsb = AutoScrollbar(self.tree_frame, orient="vertical")
        hsb = AutoScrollbar(self.tree_frame, orient="horizontal")
        self.tree = ttk.Treeview(self.tree_frame, columns=("value"), yscrollcommand=vsb.set, xscrollcommand=hsb.set, 
                                 style="Custom.Treeview", height=int(self.config_data.get("height", 20)))
        
        self.tree.heading("#0", text="Key / Index", anchor="w")
        self.tree.heading("value", text="Value", anchor="w")
        self.tree.column("#0", width=250, stretch=tk.YES)
        self.tree.column("value", width=250, stretch=tk.YES)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # 4. Footer
        self.footer = tk.Frame(self)
        self.footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        if self.allow_save_as:
            ttk.Button(self.footer, text="Save As...", command=self.save_as).pack(side=tk.LEFT, padx=2)

    def load_json(self, source):
        data = self.data_manager.load(source)
        if self.show_values_var.get():
            cols = self.data_manager.discover_columns()
            self.tree["columns"] = ("value",) + tuple(cols)
            for c in cols:
                self.tree.heading(c, text=c.replace("_", " ").title(), anchor="w")
                self.tree.column(c, width=150, stretch=tk.YES)
        else:
            self.tree["columns"] = ("value",)
        
        self.refresh_tree_display(getattr(self, 'filter_var', tk.StringVar()).get(), self.show_values_var.get())

    def browse_file(self):
        fn = filedialog.askopenfilename(title="Select JSON", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if fn: self.load_json(fn)

    def save_as(self):
        fn = filedialog.asksaveasfilename(title="Save JSON", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if fn: self.data_manager.save_as(fn)

    def _on_view_toggle(self):
        self.load_json(self.data_manager.raw_data)

    def _toggle_all(self, state):
        stack = [c for c in self.tree.get_children("")]
        while stack:
            item = stack.pop()
            self.tree.item(item, open=state)
            stack.extend(self.tree.get_children(item))

    def _draw(self):
        """Syncs backgrounds for transparency support."""
        bg = self.cget("bg")
        for f in [self.header, self.ctrl, self.footer, self.tree_frame]:
            if hasattr(f, 'config'): f.config(bg=bg)
        if hasattr(self, 'lbl'): self.lbl.config(bg=bg)
        ttk.Style().configure("Custom.Treeview", background=bg, fieldbackground=bg)

@WidgetRegistry.register("_DataJsonTree")
class BuilderDataJsonTreeCreator(TransparencyMixin):

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderDataJsonTreeCreator()
        return creator.make_data_json_tree(parent_widget, config_data, context, **kwargs)

    def make_data_json_tree(self, parent_widget, config_data, context=None, **kwargs):
        if context:
            state_mirror_engine = context.state_mirror_engine
            base_mqtt_topic = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            base_mqtt_topic = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self

        widget = JsonTreeWidget(parent_widget, config_data, state_mirror_engine, base_mqtt_topic)
        
        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(widget, None, config_data, builder_instance)
        
        path = config_data.get("path")
        if path and state_mirror_engine:
            state_mirror_engine.register_widget(path, None, base_mqtt_topic, config_data)
            state_mirror_engine.initialize_widget_state(path)

        return widget
