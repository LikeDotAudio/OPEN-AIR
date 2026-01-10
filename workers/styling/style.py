# display/styling/style.py
#
# Defines the color palettes for different UI themes, providing a centralized
# source for application-wide style configurations.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
#
# Version 20251127.000000.1

import os
import copy
import tkinter as tk
from tkinter import ttk

# --- Global Scope Variables ---
current_version = "20251127.000000.1"
current_version_hash = 20251127 * 0 * 1
current_file = f"{os.path.basename(__file__)}"

# The default theme to use. This can be changed here to easily switch the entire application's style.
DEFAULT_THEME = "dark"

# THEMES is a dictionary that holds all our color palettes.
THEMES = {
    # The "dark" theme, inspired by dark IDE color schemes.
    "dark": {
        "bg": "#2b2b2b",
        "fg": "#dcdcdc",
        "fg_alt": "#888888",
        "primary": "#3c3f41",
        "secondary": "#4e5254",
        "accent": "#f4902c",
        "hover_blue": "#4169E1",
        "text": "#ffffff",
        "border": "#555555",
        "relief": "solid",
        "border_width": 0,
        "padding": 1,
        "tab_content_padding": 1,
        # --- Styling Variables for Treeview (Table) ---
        "treeview_bg": "#3c3f41",
        "treeview_fg": "#dcdcdc",
        "treeview_field_bg": "#3c3f41",
        "treeview_heading_bg": "#4e5254",
        "treeview_heading_fg": "#dcdcdc",
        "treeview_heading_active_bg": "#55585a",
        "treeview_selected_bg": "#007acc",
        "treeview_selected_fg": "#ffffff",
        # --- Styling Variables for Tables and Entries ---
        "table_bg": "#3c3f41",
        "table_fg": "#dcdcdc",
        "table_heading_bg": "#4e5254",
        "table_border": "#555555",
        "entry_bg": "#dcdcdc",
        "entry_fg": "#000000",
        # ----------------------------------------------------
        "textbox_style": {
            "Textbox_Font": "Segoe UI",
            "Textbox_Font_size": 13,
            "Textbox_Height": 1,
            "Textbox_Font_colour": "#000000",
            "Textbox_border_colour": "#555555",
            "Textbox_BG_colour": "#dcdcdc",
        },
        "button_base_style": {
            "borderwidth": 2,
            "relief": "raised",
            "font": ("Helvetica", 13, "bold"),
            "highlightcolor": "#ffffff",
            "highlightbackground": "#555555",
            "highlightthickness": 2,
        },
        "button_style_actuator": {
            "background": "#4e5254",
            "foreground": "#ffffff",
            "font": ("Helvetica", 13, "bold"),
            "Button_Hover_Bg": "#4169E1",
            "Button_Pressed_Bg": "#f4902c",
            "Button_Disabled_Bg": "#888888",
            "Button_Disabled_Fg": "#dcdcdc",
        },
        "button_style_toggle": {
            "background": "#4e5254",
            "foreground": "#ffffff",
            "font": ("Helvetica", 13, "bold"),
            "Button_Hover_Bg": "#dcdcdc",
            "Button_Hover_Fg": "#000000",
            "Button_Pressed_Bg": "#f4902c",
            "Button_Selected_Bg": "#f4902c",
            "Button_Selected_Fg": "#ffffff",
            "Button_Disabled_Bg": "#888888",
            "Button_Disabled_Fg": "#dcdcdc",
        },
        "button_style_toggler": {
            "background": "#4e5254",
            "foreground": "#ffffff",
            "font": ("Helvetica", 13, "bold"),
            "Button_Hover_Bg": "#dcdcdc",
            "Button_Hover_Fg": "#000000",
            "Button_Pressed_Bg": "#f4902c",
            "Button_Selected_Bg": "#f4902c",
            "Button_Selected_Fg": "#ffffff",
            "Button_Disabled_Bg": "#888888",
            "Button_Disabled_Fg": "#dcdcdc",
        },
        "button_style_toggler_unselected": {
            "background": "#4e5254",
            "foreground": "#ffffff",
            "Button_Hover_Bg": "#dcdcdc",
            "Button_Hover_Fg": "#000000",
        },
        "fader_style": {
            "tick_size": 0.1,
            "tick_font_family": "Helvetica",
            "tick_font_size": 10,
            "tick_color": "light grey",
            "value_follow": True,
            "value_highlight_color": "#f4902c",
        },
        "tab_style": {
            "tab_base_style": {
                "background": "#3c3f41",
                "foreground": "#6d6d6d",
                "font": ("Helvetica", 13, "bold"),
                "padding": [10, 5],
                "borderwidth": 0,
                "relief": "flat",
                "highlightcolor": "#a5a5a5",
                "highlightbackground": "#555555",
                "highlightthickness": 0,
            },
            "tab_styles": [
                "Accent.TNotebook.Tab1",
                "Accent.TNotebook.Tab2",
                "Accent.TNotebook.Tab3",
                "Accent.TNotebook.Tab4",
                "Accent.TNotebook.Tab5",
                "Accent.TNotebook.Tab6",
                "Accent.TNotebook.Tab7",
                "Accent.TNotebook.Tab8",
                "Accent.TNotebook.Tab9",
                "Accent.TNotebook.Tab10",
            ],
        },
        "accent_colors": [
            "#996633",  # 1. Brown
            "#c75450",  # 2. Red
            "#d18616",  # 3. Orange
            "#dcdcaa",  # 4. Yellow
            "#6a9955",  # 5. Green
            "#007acc",  # 6. Blue
            "#6464a3",  # 7. Violet
            "#ce9178",  # 8. Tan
            "#b5cea8",  # 9. Gray-Green
            "#7d7d7d",  # 10. Gray
        ],
    },
    # The "light" theme, providing a high-contrast alternative.
    "light": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "fg_alt": "#555555",
        "primary": "#ffffff",
        "secondary": "#e0e0e0",
        "accent": "#0078d7",
        "hover_blue": "#4169E1",
        "text": "#000000",
        "border": "#ababab",
        "relief": "groove",
        "border_width": 0,
        "padding": 1,
        "tab_content_padding": 1,
        # --- Styling Variables for Treeview (Table) ---
        "treeview_bg": "#ffffff",
        "treeview_fg": "#000000",
        "treeview_field_bg": "#ffffff",
        "treeview_heading_bg": "#e0e0e0",
        "treeview_heading_fg": "#000000",
        "treeview_heading_active_bg": "#d0d0d0",
        "treeview_selected_bg": "#0078d7",
        "treeview_selected_fg": "#ffffff",
        # --- Styling Variables for Tables and Entries ---
        "table_bg": "#ffffff",
        "table_fg": "#000000",
        "table_heading_bg": "#e0e0e0",
        "table_border": "#ababab",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        # ----------------------------------------------------
        "textbox_style": {
            "Textbox_Font": "Segoe UI",
            "Textbox_Font_size": 13,
            "Textbox_Height": 1,
            "Textbox_Font_colour": "#000000",
            "Textbox_border_colour": "#ababab",
            "Textbox_BG_colour": "#ffffff",
        },
        "button_base_style": {
            "borderwidth": 2,
            "relief": "raised",
            "padding": [10, 5],
            "background": "#e0e0e0",
            "foreground": "#000000",
            "font": ("Helvetica", 13, "bold"),
            "highlightcolor": "#000000",
            "highlightbackground": "#e0e0e0",
            "highlightthickness": 2,
        },
        "button_style": {
            "Button_Normal_Bg": "#e0e0e0",
            "Button_Normal_Fg": "#000000",
            "Button_Hover_Bg": "#4169E1",
            "Button_Pressed_Bg": "#0078d7",
            "Button_Selected_Bg": "#0078d7",
            "Button_Selected_Fg": "#ffffff",
            "Button_Disabled_Bg": "#ababab",
            "Button_Disabled_Fg": "#555555",
        },
        "button_style_actuator": {
            "background": "#e0e0e0",
            "foreground": "#000000",
            "font": ("Helvetica", 13, "bold"),
            "pressed_bg": "#0078d7",
            "hover_bg": "#4169E1",
            "disabled_bg": "#ababab",
            "disabled_fg": "#555555",
        },
        "button_style_toggle": {
            "background": "#4e5254",
            "foreground": "#000000",
            "font": ("Helvetica", 13, "bold"),
            "pressed_bg": "#0078d7",
            "hover_bg": "#dcdcdc",
            "hover_fg": "#000000",
            "selected_bg": "#f4902c",
            "selected_fg": "#ffffff",
            "disabled_bg": "#ababab",
            "disabled_fg": "#555555",
        },
        "button_style_toggler": {
            "background": "#4e5254",
            "foreground": "#000000",
            "font": ("Helvetica", 13, "bold"),
            "pressed_bg": "#0078d7",
            "hover_bg": "#dcdcdc",
            "hover_fg": "#000000",
            "selected_bg": "#f4902c",
            "selected_fg": "#ffffff",
            "disabled_bg": "#ababab",
            "disabled_fg": "#555555",
        },
        "button_style_toggler_unselected": {
            "background": "#4e5254",
            "foreground": "#000000",
            "hover_bg": "#dcdcdc",
            "hover_fg": "#000000",
        },
        "fader_style": {
            "tick_size": 0.1,
            "tick_font_family": "Helvetica",
            "tick_font_size": 10,
            "tick_color": "dark grey",
            "value_follow": True,
            "value_highlight_color": "#0078d7",
        },
        "tab_style": {
            "tab_base_style": {
                "background": "#f0f0f0",
                "foreground": "#000000",
                "font": ("Helvetica", 13, "bold"),
                "padding": [10, 5],
                "borderwidth": 0,
                "relief": "flat",
                "highlightcolor": "#000000",
                "highlightbackground": "#e0e0e0",
                "highlightthickness": 0,
            },
            "tab_styles": [
                "Accent.TNotebook.Tab1",
                "Accent.TNotebook.Tab2",
                "Accent.TNotebook.Tab3",
                "Accent.TNotebook.Tab4",
                "Accent.TNotebook.Tab5",
                "Accent.TNotebook.Tab6",
                "Accent.TNotebook.Tab7",
                "Accent.TNotebook.Tab8",
                "Accent.TNotebook.Tab9",
                "Accent.TNotebook.Tab10",
            ],
        },
        "accent_colors": [
            "#A0522D",  # 1. Brown (Sienna)
            "#D22B2B",  # 2. Red (Firebrick)
            "#FF8C00",  # 3. Orange (DarkOrange)
            "#FFD700",  # 4. Yellow (Gold)
            "#228B22",  # 5. Green (ForestGreen)
            "#4169E1",  # 6. Blue (RoyalBlue)
            "#8A2BE2",  # 7. Violet (BlueViolet)
            "#D2691E",  # 8. Tan (Chocolate)
            "#556B2F",  # 9. Gray-Green (DarkOliveGreen)
            "#7d7d7d",  # 10. Gray
        ],
    },
}
