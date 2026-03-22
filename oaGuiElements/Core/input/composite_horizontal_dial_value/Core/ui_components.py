# Core/ui_components.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk

class CompositeUIComponents:
    """Builder methods for the sub-components of the composite fader."""

    @staticmethod
    def build_label(ctx):
        """Constructs the top-level label canvas."""
        f_label = tk.Canvas(ctx['sub_frame'], bd=0, highlightthickness=0, height=25, bg=ctx['p_bg'])
        f_label.grid(row=0, column=0, sticky="nsew", padx=5)
        ctx['trans_mgr'].apply_transparency(f_label, f_label, ctx['config_data'], ctx['builder_instance'])
        
        def draw_f_label(e=None):
            if not f_label.winfo_exists(): return
            f_label.delete("all")
            f_label.create_text(5, 23, text=ctx['label_text'].upper(), fill="#888888", font=("Helvetica", 8, "bold"), anchor="sw")
        f_label.bind("<Configure>", draw_f_label)
        return f_label, draw_f_label

    @staticmethod
    def build_entry(ctx):
        """Constructs the numeric entry field inside a container canvas."""
        val_container = tk.Canvas(ctx['sub_frame'], bd=0, highlightthickness=0, height=35, bg=ctx['p_bg'])
        val_container.grid(row=0, column=2, sticky="nsew", padx=5)
        
        v_config_exists = "value_config" in ctx['config_data']
        val_container._oca_path = f"{ctx['path']}.value_config" if v_config_exists else ctx['path']
        ctx['trans_mgr'].apply_transparency(val_container, val_container, ctx['config_data'], ctx['builder_instance'])

        clean_path = ctx['path'].replace('/', '_') if ctx['path'] else "default"
        style_name = f"CompVal.{clean_path}.TEntry"
        style = ttk.Style()
        
        def sync_entry_style():
            if not val_container.winfo_exists(): return
            bg = val_container.cget("bg")
            style.configure(style_name, fieldbackground=bg, foreground=ctx['v_text_color'], 
                            insertcolor="white", font=("Helvetica", ctx['v_font_size']))

        entry = ttk.Entry(val_container, width=ctx['v_width'], style=style_name, 
                          textvariable=ctx['entry_string_var'], justify=tk.CENTER)
        entry.place(relx=0.5, rely=0.5, anchor="center")
        
        entry.bind("<FocusOut>", ctx['on_manual_cb'])
        entry.bind("<Return>", ctx['on_manual_cb'])
        
        return val_container, entry, sync_entry_style

    @staticmethod
    def build_unit_label(ctx):
        """Constructs the units label canvas."""
        unit_label = tk.Canvas(ctx['sub_frame'], bd=0, highlightthickness=0, height=25, bg=ctx['p_bg'])
        unit_label.grid(row=1, column=2, sticky="nsew", padx=5)
        ctx['trans_mgr'].apply_transparency(unit_label, unit_label, ctx['config_data'], ctx['builder_instance'])
        
        def draw_unit_label(e=None):
            if not unit_label.winfo_exists(): return
            unit_label.delete("all")
            unit_label.create_text(unit_label.winfo_width()/2, 5, text=ctx['units_txt'], 
                                   fill="#888888", font=("Helvetica", ctx['v_font_size']-1), anchor="n")
        unit_label.bind("<Configure>", draw_unit_label)
        return unit_label, draw_unit_label
