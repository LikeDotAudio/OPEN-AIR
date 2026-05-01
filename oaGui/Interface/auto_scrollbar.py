# Interface/auto_scrollbar.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: An industrial scrollbar that manages its own visibility based on content scale.

from tkinter import ttk

class AutoScrollbar(ttk.Scrollbar):
    """An industrial scrollbar that manages its own visibility based on content scale."""
    def __init__(self, master=None, **kwargs):
        self.grid_kwargs = {}
        super().__init__(master, **kwargs)

    def grid(self, **kwargs):
        self.grid_kwargs.update(kwargs)
        super().grid(**kwargs)

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid(**self.grid_kwargs)
        ttk.Scrollbar.set(self, lo, hi)
