import tkinter as tk
from tkinter import ttk

class CompositeUIComponents:
    """Builder methods for the sub-components of the composite fader."""

    @staticmethod
    def build_label(sub_frame, label_text, p_bg, trans_mgr, builder_instance, config_data):
        f_label = tk.Canvas(sub_frame, bd=0, highlightthickness=0, height=25, bg=p_bg)
        f_label.grid(row=0, column=0, sticky="nsew", padx=5)
        trans_mgr.apply_transparency(f_label, f_label, config_data, builder_instance)
        
        def draw_f_label(e=None):
            if not f_label.winfo_exists(): return
            f_label.delete("all")
            f_label.create_text(5, 23, text=label_text.upper(), fill="#888888", font=("Helvetica", 8, "bold"), anchor="sw")
        f_label.bind("<Configure>", draw_f_label)
        return f_label, draw_f_label

    @staticmethod
    def build_entry(sub_frame, v_width, v_font_size, v_text_color, entry_string_var, p_bg, path, trans_mgr, builder_instance, config_data, on_manual_cb):
        val_container = tk.Canvas(sub_frame, bd=0, highlightthickness=0, height=35, bg=p_bg)
        val_container.grid(row=0, column=2, sticky="nsew", padx=5)
        v_config_exists = "value_config" in config_data
        val_container._oca_path = f"{path}.value_config" if v_config_exists else path
        trans_mgr.apply_transparency(val_container, val_container, config_data, builder_instance)

        clean_path = path.replace('/', '_') if path else "default"
        style_name = f"CompVal.{clean_path}.TEntry"
        style = ttk.Style()
        
        def sync_entry_style():
            if not val_container.winfo_exists(): return
            bg = val_container.cget("bg")
            style.configure(style_name, fieldbackground=bg, foreground=v_text_color, insertcolor="white", font=("Helvetica", v_font_size))

        entry = ttk.Entry(val_container, width=v_width, style=style_name, textvariable=entry_string_var, justify=tk.CENTER)
        entry.place(relx=0.5, rely=0.5, anchor="center")
        
        entry.bind("<FocusOut>", on_manual_cb)
        entry.bind("<Return>", on_manual_cb)
        
        return val_container, entry, sync_entry_style

    @staticmethod
    def build_unit_label(sub_frame, units_txt, v_font_size, p_bg, trans_mgr, builder_instance, config_data):
        unit_label = tk.Canvas(sub_frame, bd=0, highlightthickness=0, height=25, bg=p_bg)
        unit_label.grid(row=1, column=2, sticky="nsew", padx=5)
        trans_mgr.apply_transparency(unit_label, unit_label, config_data, builder_instance)
        
        def draw_unit_label(e=None):
            if not unit_label.winfo_exists(): return
            unit_label.delete("all")
            unit_label.create_text(unit_label.winfo_width()/2, 5, text=units_txt, fill="#888888", font=("Helvetica", v_font_size-1), anchor="n")
        unit_label.bind("<Configure>", draw_unit_label)
        return unit_label, draw_unit_label
