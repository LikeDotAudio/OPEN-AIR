# listbox/listbox.py
import inspect

# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized dynamic Listbox widget.
import tkinter as tk
from tkinter import ttk

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Methods.i18n_utils import get_text

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Workers.transparency.transparency import TransparencyManager
from oaGui.Workers.transparency.transparency_mixin import TransparencyMixin
from oaStyle.Core.style import DEFAULT_THEME, THEMES

# --- EXTRACTED CORE MODULES ---
from .listbox_options import ListboxOptionsManager
from .listbox_sync_engine import ListboxSyncEngine


class BuilderListboxCreator(TransparencyMixin):
    """Mixin for creating a dynamic Listbox with MQTT sync and industrial transparency."""

    def make_listbox(self, parent_widget, config_data, context=None, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️📑 [BUILDER] Creating Listbox widget.", level="TRACE")

        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        label, path = get_text(config.get("label_active"), ""), config_data.get("path")

        # 1. Scaffolding
        sub_frame = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", width=200, height=150)
        sub_frame.pack_propagate(False); sub_frame.grid_rowconfigure(1, weight=1); sub_frame.grid_columnconfigure(0, weight=1)

        if hasattr(self, '_apply_transparency'):
            TransparencyManager.apply_transparency(sub_frame, sub_frame, config_data, b_inst)

        # 2. Components
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        lb_frame = tk.Frame(sub_frame, bd=0, highlightthickness=0)
        lb_frame.grid(row=1, column=0, sticky="nsew", pady=(25 if label else 2, 2))
        lb_frame.grid_rowconfigure(0, weight=1); lb_frame.grid_columnconfigure(0, weight=1)

        vsb = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        listbox = tk.Listbox(lb_frame, yscrollcommand=vsb.set, exportselection=False, selectmode=tk.SINGLE, borderwidth=0, highlightthickness=1,
                             fg=colors.get("treeview_fg", "#dcdcdc"), selectbackground=colors.get("treeview_selected_bg", "#007acc"),
                             selectforeground=colors.get("treeview_selected_fg", "#ffffff"), highlightbackground=colors.get("border", "#555"))
        vsb.config(command=listbox.yview); vsb.grid(row=0, column=1, sticky="ns"); listbox.grid(row=0, column=0, sticky="nsew")

        # 3. State & Options
        om = ListboxOptionsManager(config_data.get("options", {}))
        var = tk.StringVar(sub_frame)

        def rebuild_display():
            listbox.delete(0, tk.END); curr_val = var.get()
            for k, opt in om.get_sorted_active():
                lbl = opt.get("label_active", k); listbox.insert(tk.END, lbl)
                if str(opt.get("value", k)) == str(curr_val):
                    idx = listbox.get(0, tk.END).index(lbl); listbox.select_set(idx); listbox.see(idx)

        def sync_bg():
            bg = sub_frame.cget("bg"); lb_frame.config(bg=bg); listbox.config(bg=bg)
            sub_frame.delete("industrial_text")
            if label: sub_frame.create_text(5, 12, text=label, anchor="w", fill="white", font=("Arial", 10, "bold"), tags="industrial_text")

        sub_frame._draw = sync_bg; sub_frame.bind("<Configure>", lambda e: sync_bg())

        # 4. Sync & Events
        var.trace_add("write", lambda *a: ListboxSyncEngine.sync_listbox_to_var(listbox, var, om.options_map))
        listbox.bind("<<ListboxSelect>>", lambda e: ListboxSyncEngine.handle_selection(listbox, var, om.options_map, path, ctx.state_mirror_engine, ctx.base_mqtt_topic_from_path))

        if path and ctx.state_mirror_engine:
            topic = ctx.state_mirror_engine.register_widget(path, var, ctx.base_mqtt_topic_from_path, config_data)
            if ctx.subscriber_router and topic: ctx.subscriber_router.subscribe_to_topic(topic, ctx.state_mirror_engine.sync_incoming_mqtt_to_gui)

            # Wildcard options update
            opt_prefix = ctx.state_mirror_engine.calculate_topic(f"{path}/options", ctx.base_mqtt_topic_from_path)
            def _on_opt_mqtt(message):
                result = om.process_mqtt_update(message.topic, message.payload, opt_prefix)
                if result:
                    rebuild_display()
                    if isinstance(result, str): var.set(om.options_map[result].get("value", result))
            if ctx.subscriber_router: ctx.subscriber_router.subscribe_to_topic(opt_prefix + "/#", _on_opt_mqtt)

            var.trace_add("write", lambda *a: ctx.state_mirror_engine.broadcast_gui_change_to_mqtt(path))
            ctx.state_mirror_engine.initialize_widget_state(path)

        rebuild_display(); sync_bg()
        return sub_frame
