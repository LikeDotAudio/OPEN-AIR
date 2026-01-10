# builder_hidden/hidden_BreakLine.py
#
# A mixin for creating a horizontal break line (Separator).
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
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk

class BreakLineCreatorMixin:
    """A mixin for creating a horizontal break line (Separator)."""

    def _create_break_line(self, parent_widget, config_data, **kwargs):
        """Creates a horizontal break line."""
        frame = ttk.Frame(parent_widget)
        separator = ttk.Separator(frame, orient='horizontal')
        separator.pack(fill='x', expand=True, padx=5, pady=5)
        return frame
