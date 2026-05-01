# oaGui/Workers/transparency/transparency.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Centralized engine for Industrial Transparency.

import tkinter as tk
import gc

from oaLogging.Methods.matrix_gate import matrix_log
from oaStyle.Constants.geometry import DEFAULT_THEME_BACKGROUND
from oaGui.Methods.transparency_config_parser import TransparencyConfigParser
from oaGui/Workers/transparency.background_slicer import BackgroundSlicer

class TransparencyManager:
    """
    Orchestrates the application of transparency and background slicing to widgets.
    """
    @staticmethod
    def cleanup(builder):
        if hasattr(builder, '_slicing_registry'):
            builder._slicing_registry.clear()
        gc.collect()

    @staticmethod
    def apply_transparency(widget, canvas, configuration, builder):
        if not widget or not builder: return
        # ⚡ HARDENING: If builder is a widget, it's a legacy call or mis-injection.
        if isinstance(builder, tk.Widget):
            return

        # ⚡ RENDER TIER BYPASS: Skip transparency registration in Fast/Ghost modes
        render_tier = getattr(builder, '_render_tier', 'high_res')
        if render_tier in ['fast', 'ghost']:
            theme_background = DEFAULT_THEME_BACKGROUND
            if hasattr(builder, 'theme_colors'):
                theme_background = builder.theme_colors.get("bg", theme_background)

            try:
                if widget.winfo_exists(): widget.configure(bg=theme_background)
                if canvas and canvas.winfo_exists(): canvas.configure(bg=theme_background)
            except: pass
            return

        widget_name = getattr(widget, 'path', type(widget).__name__)

        try:
            TransparencyManager._register_widget_for_slicing(widget, canvas, configuration, builder, widget_name)
        except Exception as e:
            TransparencyManager._handle_registration_failure(widget, widget_name, e)

    @staticmethod
    def _register_widget_for_slicing(widget, canvas, configuration, builder, widget_name):
        bg_string, is_solid, is_transparent = TransparencyConfigParser.parse_configuration(configuration, widget)

        # ⚡ OPTIMIZATION: Only register if transparency is explicitly requested or expected.
        if not is_transparent or (is_solid and not is_transparent):
            return

        slicer = BackgroundSlicer(widget, canvas, builder, widget_name)

        widget._perform_background_slice = slicer.perform_slice

        if hasattr(builder, 'register_for_slicing'):
            builder.register_for_slicing(slicer.perform_slice)
        widget.bind("<Map>", lambda event: slicer.perform_slice(), add="+")

    @staticmethod
    def _handle_registration_failure(widget, widget_name, e):
        matrix_log("ui", "transparency", "apply_transparency", f"❌ TransparencyManager: Failed to apply to {widget_name}: {e}", "ERROR")
        if widget.winfo_exists() and isinstance(widget, tk.Canvas):
            widget.create_text(10, 10, text=f"Transparency Error: {e}", fill="red", anchor="nw")
