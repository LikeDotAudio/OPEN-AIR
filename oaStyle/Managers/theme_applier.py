# Managers/theme_applier.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
from ..Core.style import THEMES, DEFAULT_THEME

def apply_theme(widget_or_root, theme_name=DEFAULT_THEME):
    """Applies global TTK styles to a Tkinter instance."""
    colors = THEMES.get(theme_name, THEMES["dark"])
    style = ttk.Style(widget_or_root)
    style.theme_use("clam")

    # Global style configuration
    style.configure(
        ".",
        background=colors["bg"],
        foreground=colors["fg"],
        font=("Helvetica", 10),
        padding=colors["padding"],
        borderwidth=colors["border_width"],
    )

    # Frame style
    style.configure("TFrame", background=colors["bg"])
    # 2026-02-24 00:40:00 - UI Flattening Start
    style.configure("Dark.TFrame", background="#000000") # Fixed black for custom modules

    # Label style
    style.configure("Dark.TLabel", background="#000000", foreground="#ffffff")

    # Button styles
    dark_grey = colors.get("secondary", "#4e5254")
    
    # Safely get toggle style
    toggle_style = THEMES[theme_name].get("button_style_toggle", {})
    selected_orange = toggle_style.get("Button_Selected_Bg", "#f4902c")
    selected_fg = toggle_style.get("Button_Selected_Fg", "#ffffff")
    hover_bg = toggle_style.get("Button_Hover_Bg", "#dcdcdc")
    hover_fg = toggle_style.get("Button_Hover_Fg", "#000000")

    style.configure(
        "TButton",
        background=dark_grey,
        foreground=colors["text"],
        font=("Helvetica", 10, "bold"),
        anchor="center",
    )
    style.map(
        "TButton",
        background=[("active", hover_bg), ("!active", dark_grey)],
        foreground=[("active", hover_fg), ("!active", colors["text"])],
    )

    # Custom Toggler style (for unselected state)
    toggler_style = THEMES[theme_name].get("button_style_toggler_unselected", {})
    toggler_unselected_bg = toggler_style.get("background", "#4e5254")
    toggler_unselected_fg = toggler_style.get("foreground", "#ffffff")
    toggler_hover_bg = toggler_style.get("Button_Hover_Bg", "#dcdcdc")
    toggler_hover_fg = toggler_style.get("Button_Hover_Fg", "#000000")

    style.configure(
        "Custom.TogglerUnselected.TButton",
        background=toggler_unselected_bg,
        foreground=toggler_unselected_fg,
        font=("Helvetica", 10, "bold"),
        anchor="center",
    )
    style.map(
        "Custom.TogglerUnselected.TButton",
        background=[("active", toggler_hover_bg), ("!active", toggler_unselected_bg)],
        foreground=[("active", toggler_hover_fg), ("!active", toggler_unselected_fg)],
    )

    # Custom Selected style
    style.configure(
        "Custom.Selected.TButton",
        background=selected_orange,
        foreground=selected_fg,
        relief="sunken",
        font=("Helvetica", 10, "bold"),
        anchor="center",
    )
    style.map(
        "Custom.Selected.TButton",
        background=[("active", hover_bg), ("!active", selected_orange)],
        foreground=[("active", hover_fg), ("!active", selected_fg)],
    )

    # 1. Notebook Container Flattening (TNotebook)
    style.configure(
        "TNotebook",
        background="black",
        borderwidth=0,
        bordercolor="black",
        darkcolor="black",
        lightcolor="black",
    )
    
    # 2. Tab Element Styling & State Mapping (TNotebook.Tab)
    style.configure(
        "TNotebook.Tab",
        background="black",
        foreground="white",
        bordercolor="black",
        lightcolor="black",
        padding=[10, 2],
        font=("Helvetica", 13),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", "#1a1a1a"), ("active", "#333333")],
        foreground=[("selected", "#ff9900")], # Signature orange
        font=[
            ("selected", ("Helvetica", 15, "bold")),
            ("!selected", ("Helvetica", 13)),
        ],
    )

    # 3. Divider / Sash Harmonization (TPanedwindow & Sash)
    style.configure(
        "TPanedwindow",
        background="black",
    )
    style.configure(
        "Sash",
        background="#111111", # Very dark grey divider
        bordercolor="black",
        lightcolor="black",
        darkcolor="black",
        sashthickness=4,
    )

    # 4. Global Treeview (Table) Styling
    style.configure(
        "Treeview",
        background="#000000",
        foreground="#dcdcdc",
        fieldbackground="#000000",
        borderwidth=0,
        font=("Helvetica", 10),
        rowheight=25
    )
    style.configure(
        "Treeview.Heading",
        background="#1a1a1a",
        foreground="#ffffff",
        relief="flat",
        font=("Helvetica", 10, "bold")
    )
    style.map(
        "Treeview",
        background=[("selected", "#333333")],
        foreground=[("selected", "#ff9900")]
    )
    
    # 2026-02-24 00:40:00 - UI Flattening End

    return colors
