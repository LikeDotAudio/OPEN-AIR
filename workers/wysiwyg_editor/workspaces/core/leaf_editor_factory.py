import tkinter as tk
from tkinter import ttk, colorchooser
from ..core.state_manager import state_manager

class LeafEditorFactory:
    """Spawns specialized editor widgets for leaf JSON properties."""

    @staticmethod
    def create(parent, key, value, full_path, source_instance):
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        
        lbl = tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#cccccc", width=15, anchor="e")
        lbl.pack(side="left")
        
        is_color = "color" in key.lower() or "colour" in key.lower() or (isinstance(value, str) and value.startswith("#") and len(value) in [4, 7])

        if is_color:
            editor = LeafEditorFactory._create_color_editor(f, key, value, full_path, source_instance)
        else:
            editor = LeafEditorFactory._create_text_editor(f, key, value, full_path, lbl, source_instance)
            
        return f

    @staticmethod
    def _create_color_editor(parent, key, value, full_path, source):
        bg = str(value).lower()
        if bg == "transparent" or not bg.startswith("#"): bg = "#2b2b2b"
        
        swatch = tk.Canvas(parent, width=25, height=18, bg=bg, highlightthickness=1, cursor="hand2")
        swatch.pack(side="left", padx=(10, 5))
        
        entry = ttk.Entry(parent, style="Property.TEntry")
        entry.insert(0, str(value))
        entry.pack(side="left", fill="x", expand=True)

        def pick(e):
            res = colorchooser.askcolor(title=f"Color: {key}", initialcolor=entry.get() or "#fff")
            if res[1]:
                swatch.config(bg=res[1]); entry.delete(0, tk.END); entry.insert(0, res[1])
                state_manager.update_state(res[1], path=full_path, source=source)
        swatch.bind("<Button-1>", pick)
        LeafEditorFactory._bind_entry_focus(parent, entry, lbl=None, full_path=full_path, old_val=value, source=source)
        return entry

    @staticmethod
    def _create_text_editor(parent, key, value, full_path, lbl, source):
        entry = ttk.Entry(parent, style="Property.TEntry")
        entry.insert(0, str(value))
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        if isinstance(value, (int, float)):
            lbl.config(cursor="sb_h_double_arrow")
            def start_scrub(e):
                source.scrub_start_val = value
                source.scrub_start_x = e.x_root
            def scrub(e):
                delta = (e.x_root - source.scrub_start_x) // 2
                new_v = source.scrub_start_val + (delta * 0.1 if isinstance(value, float) else delta)
                entry.delete(0, tk.END); entry.insert(0, f"{new_v:.3f}".rstrip('0').rstrip('.') if isinstance(value, float) else str(int(new_v)))
                state_manager.update_state(new_v, path=full_path, source=source)
            lbl.bind("<Button-1>", start_scrub)
            lbl.bind("<B1-Motion>", scrub)

        LeafEditorFactory._bind_entry_focus(parent, entry, lbl, full_path, value, source)
        return entry

    @staticmethod
    def _bind_entry_focus(frame, entry, lbl, full_path, old_val, source):
        def focus_in(e): frame.config(bg="#444444"); 
        if lbl: lbl.config(bg="#444444", fg="#33A1FD")
        
        def focus_out(e):
            frame.config(bg="#2b2b2b"); 
            if lbl: lbl.config(bg="#2b2b2b", fg="#cccccc")
            v = entry.get()
            try:
                if v.lower() == "true": final = True
                elif v.lower() == "false": final = False
                elif v.startswith("#"): final = v 
                else: final = float(v) if "." in v else int(v)
                if final != old_val: state_manager.update_state(final, path=full_path, source=source)
            except: pass

        entry.bind("<FocusIn>", focus_in)
        entry.bind("<FocusOut>", focus_out)
        entry.bind("<Return>", lambda e: source.focus_set())
