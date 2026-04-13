# Core/ptp_dissector_engine.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

class PTPDissectorEngine:
    """Handles recursive population of the PTP packet dissector tree."""

    @staticmethod
    def populate(tree, parent, data):
        """Recursively inserts dictionary/list data into the Treeview."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    node = tree.insert(parent, "end", text=key, open=True)
                    PTPDissectorEngine.populate(tree, node, value)
                else:
                    tree.insert(parent, "end", text=key, values=(value))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    node = tree.insert(parent, "end", text=f"[{i}]", open=True)
                    PTPDissectorEngine.populate(tree, node, item)
                else:
                    tree.insert(parent, "end", text=f"[{i}]", values=(item))
