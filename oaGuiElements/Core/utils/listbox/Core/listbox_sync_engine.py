# Core/listbox_sync_engine.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import time
import orjson

class ListboxSyncEngine:
    """Orchestrates synchronization between tk.StringVar, the Listbox widget, and MQTT topics."""

    @staticmethod
    def sync_listbox_to_var(listbox, var, options_map):
        """Updates the Listbox selection highlight to match the StringVar value."""
        val = var.get()
        listbox.select_clear(0, tk.END)
        if not val: return

        target_lbl = None
        for k, opt in options_map.items():
            if str(opt.get("value", k)) == str(val):
                target_lbl = opt.get("label_active", k); opt["selected"] = "true"
            else: opt["selected"] = "false"

        if target_lbl and target_lbl in listbox.get(0, tk.END):
            idx = listbox.get(0, tk.END).index(target_lbl)
            listbox.select_set(idx); listbox.see(idx)

    @staticmethod
    def handle_selection(listbox, var, options_map, path, engine, base_topic):
        """Processes a manual UI selection and broadcasts state to multiple MQTT topics."""
        sel = listbox.curselection()
        if not sel: return
        lbl = listbox.get(sel[0])
        
        selected_key = next((k for k, opt in options_map.items() if opt.get("label_active", k) == lbl), None)
        if not selected_key: return

        val = options_map[selected_key].get("value", selected_key)
        
        # 1. Update selection status for ALL options via MQTT
        for k, opt in options_map.items():
            tp = engine.calculate_topic(f"{path}/options/{k}/selected", base_topic)
            engine.publish_command(tp, orjson.dumps({"val": k == selected_key, "ts": time.time()}).decode())

        # 2. Update main variable
        var.set(val)