import tkinter as tk
from managers.Display.transparency.transparency import TransparencyManager

class StructuralAssembler:
    """Manages the immediate creation of structural containers (OcaBlock, OcaBin)."""

    @staticmethod
    def create_block(parent, value, builder):
        target = tk.Canvas(parent, bd=0, relief="flat", highlightthickness=0, bg="#2b2b2b")
        if builder and hasattr(builder, 'show_structure') and builder.show_structure.get():
            target.config(highlightbackground="red", highlightthickness=1)
        TransparencyManager.apply_transparency(target, target, value, builder)
        return target

    @staticmethod
    def create_bin(parent, value, builder):
        hull = tk.Frame(parent, bg="#2b2b2b", bd=0, highlightthickness=0)
        hull.grid_rowconfigure(0, weight=1); hull.grid_columnconfigure(0, weight=1)
        
        viewport = tk.Canvas(hull, bd=0, highlightthickness=0, bg="#2b2b2b")
        viewport.grid(row=0, column=0, sticky="nsew")
        
        inner = tk.Frame(viewport, bg="#2b2b2b", bd=0, highlightthickness=0)
        inner_id = viewport.create_window((0, 0), window=inner, anchor="nw")
        
        inner.bind("<Configure>", lambda e: viewport.configure(scrollregion=viewport.bbox("all")) if viewport.winfo_exists() else None)
        
        TransparencyManager.apply_transparency(hull, viewport, value, builder)
        TransparencyManager.apply_transparency(hull, inner, value, builder)
        return hull, inner
