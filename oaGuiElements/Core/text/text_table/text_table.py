# text_table/text_table.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Editable Table Widget.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from tkinter import ttk
import orjson
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaComMQTT.Core import mqtt_publisher_service
from .table_editing import TableEditingManager
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from .Core.table_csv_service import TableCSVService
from .Core.table_sync_engine import TableSyncEngine

class BuilderTextTableCreator(TransparencyMixin):
    """Mixin for creating an editable table widget with CSV backup and MQTT sync."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderTextTableCreator()
        return creator.make_text_table(parent_widget, config_data, context, **kwargs)

    def make_text_table(self, parent_widget, config_data, context=None, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📑 [BUILDER] Creating Table widget.", level="TRACE")
        
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        
        # 1. Container & Scaffolding
        container = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat")
        container.grid_rowconfigure(0, weight=1); container.grid_columnconfigure(0, weight=1)
        
        if hasattr(self, '_apply_transparency'): self._apply_transparency(container, container, config_data, b_inst)

        # ⚡ Path Resolution: Use config or passed kwargs
        path = config_data.get("path") or kwargs.get("path")
        abs_topic = ctx.state_mirror_engine.calculate_topic(path, ctx.base_mqtt_topic_from_path)
        csv_svc = TableCSVService(config_data.get("label_active", "Table"))
        
        # 2. Treeview
        headers = config_data.get("headers", [])
        tree = ttk.Treeview(container, show="headings", columns=headers, height=config_data.get("height", 10), style="Custom.Treeview")
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=config_data.get("column_width", 120), anchor="w")
        
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns"); hsb.grid(row=1, column=0, sticky="ew")

        # 3. State & Sync
        item_map, device_key_map = {}, {}
        sync = TableSyncEngine(tree, item_map, device_key_map, abs_topic, csv_svc, builder_logger)
        tree.editor = TableEditingManager(tree, ctx.state_mirror_engine, abs_topic, 
                                          allow_sort=config_data.get("allow_sort", True), allow_undo=config_data.get("allow_undo", True))

        def _on_csv_read():
            sync.is_reading_csv = True
            data = csv_svc.load()
            if data: sync.update_full(data)
            sync.is_reading_csv = False

        # 4. Buttons
        bf = tk.Frame(container); bf.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5,0))
        btns = [("Write CSV", lambda: csv_svc.save(tree["columns"], item_map)), ("Read CSV", _on_csv_read),
                ("Add Row", tree.editor.add_row), ("Delete Row", tree.editor.delete_selection), ("Undo", tree.editor.undo)]
        for lbl, cmd in btns:
            if config_data.get(lbl.replace(" ", "_"), True): ttk.Button(bf, text=lbl, command=cmd).pack(side=tk.LEFT, padx=2)

        def sync_bg():
            bg = container.cget("bg"); bf.config(bg=bg); ttk.Style().configure("Custom.Treeview", background=bg, fieldbackground=bg)
        container._draw = sync_bg

        # 5. Events & Registration
        def _on_select(e):
            sel = tree.selection()
            if sel and path:
                sd = item_map.get(sel[0]); tp = ctx.state_mirror_engine.calculate_topic(f"{path}/selected", ctx.base_mqtt_topic_from_path)
                mqtt_publisher_service.publish_payload(tp, orjson.dumps({"val": sd}).decode())
        tree.bind("<<TreeviewSelect>>", _on_select)

        if path:
            ctx.state_mirror_engine.register_widget(path, tk.StringVar(), ctx.base_mqtt_topic_from_path, config_data, update_callback=sync.update_full)
            if abs_topic: ctx.subscriber_router.subscribe_to_topic(abs_topic + "/#", sync.update_incremental)
            
            def _cleanup(e):
                if e.widget == str(container): ctx.subscriber_router.unsubscribe_from_topic(abs_topic + "/#", sync.update_incremental)
            container.bind("<Destroy>", _cleanup)

            if not ctx.state_mirror_engine.initialize_widget_state(path):
                if config_data.get("data"): sync.update_full(config_data.get("data"), suppress_mqtt=True)
                else: csv_svc.save(tree["columns"], item_map)

        return container
