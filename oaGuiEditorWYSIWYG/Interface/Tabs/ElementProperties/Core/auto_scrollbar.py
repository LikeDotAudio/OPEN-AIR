# Interface/Tabs/ElementProperties/Core/auto_scrollbar.py
# Author: Anthony Peter Kuzub
# Version: 20260417.001.0
#
# Description: A scrollbar that hides itself when the content fits the viewport.

from tkinter import ttk

class AutoScrollbar(ttk.Scrollbar):
    """A custom scrollbar that removes itself from the grid if the scroll region is smaller than the frame."""
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
        super().set(lo, hi)
