from tkinter import ttk
from workers.styling.style import THEMES

class GuiStyleMixin:
    """Handles Theming."""
    def _apply_styles(self, theme_name):
        style = ttk.Style()
        colors = THEMES.get(theme_name, THEMES["dark"])

        bg = colors.get("bg", "#2b2b2b")
        fg = colors.get("fg", "#dcdcdc")
        entry_bg = colors.get("entry_bg", "#dcdcdc")
        entry_fg = colors.get("entry_fg", "#000000")
        accent = colors.get("accent", "#f4902c")

        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg, foreground=fg)

        style.configure('TEntry', fieldbackground=entry_bg, background=bg, foreground=entry_fg, bordercolor=colors.get("border", "#555555"))
        style.map('TEntry', fieldbackground=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))],
                  background=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))])

        style.configure('Custom.TEntry', fieldbackground=entry_bg, background=bg, foreground=entry_fg, bordercolor=colors.get("border", "#555555"))
        style.map('Custom.TEntry', fieldbackground=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))],
                  background=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))])

        style.configure('TCombobox', fieldbackground=entry_bg, background=bg, foreground=entry_fg, bordercolor=colors.get("border", "#555555"), selectbackground=accent, selectforeground=entry_fg)
        style.map('TCombobox', fieldbackground=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))],
                  background=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))])

        style.configure("TCombobox.Listbox", background=entry_bg, foreground=entry_fg, selectbackground=accent, selectforeground=fg)

        style.configure('BlackText.TCombobox', foreground=entry_fg)
        style.map('BlackText.TCombobox', fieldbackground=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))],
                  background=[('readonly', entry_bg), ('disabled', colors.get("fg_alt", "#888888"))])

        tab_style_config = colors.get("tab_style", {}).get("tab_base_style", {})
        style.configure('TNotebook', background=bg, borderwidth=0)
        style.configure('TNotebook.Tab',
                        background=tab_style_config.get("background", colors.get("primary", bg)),
                        foreground=tab_style_config.get("foreground", fg),
                        font=('Helvetica', 12),  # Default to regular for unselected
                        padding=[colors["padding"] * 10, colors["padding"] * 5],  # Define padding directly here
                        borderwidth=tab_style_config.get("borderwidth", 0),
                        relief="flat")
        style.map('TNotebook.Tab',
                  background=[('selected', accent), ('!selected', colors.get("secondary", bg))],
                  foreground=[('selected', colors["accent_colors"][5]), ('!selected', fg)],  # Darker blue
                  font=[('selected', ('Helvetica', 14, 'bold')), ('!selected', ('Helvetica', 12))])  # +2 points

        # Custom Button Style
        style.configure('Custom.TButton', background=colors.get('secondary'), foreground=colors.get('fg'))
        style.map('Custom.TButton',
                  background=[('pressed', accent), ('active', colors.get('hover_blue'))])

        # Custom Selected Button Style (for ON state)
        style.configure('Custom.Selected.TButton', background=accent, foreground=colors.get('fg'))
        style.map('Custom.Selected.TButton',
                  background=[('pressed', accent), ('active', colors.get('hover_blue'))])

        # Treeview Style
        style.configure("Custom.Treeview",
                        background=colors.get("treeview_bg", colors["bg"]),
                        foreground=colors.get("treeview_fg", colors["fg"]),
                        fieldbackground=colors.get("treeview_field_bg", colors["bg"]),
                        rowheight=25)
        style.map("Custom.Treeview",
                  background=[('selected', colors.get("treeview_selected_bg", colors["accent"]))],
                  foreground=[('selected', colors.get("treeview_selected_fg", colors["fg"]))])

        style.configure("Custom.Treeview.Heading",
                        background=colors.get("treeview_heading_bg", colors["primary"]),
                        foreground=colors.get("treeview_heading_fg", colors["fg"]),
                        relief="flat")
        style.map("Custom.Treeview.Heading",
                  background=[('active', colors.get("treeview_heading_active_bg", colors["secondary"]))])
