# oaGui/FileReaders/scanner/widget_attachment_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for safely attaching widget instances to parent containers.

import tkinter as tk

def attach_widget_to_parent(parent, instance, index=0):
    """Safely adds a widget instance to a parent using the appropriate geometry manager."""
    if not instance: 
        return
    
    manager = None
    if parent.winfo_children():
        manager = parent.winfo_children()[0].winfo_manager()

    if manager == "grid":
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(index, weight=1)
        instance.grid(row=index, column=0, sticky="nsew")
    elif manager == "pack":
        instance.pack(fill=tk.BOTH, expand=True)
    else:
        # Default fallback to grid
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(index, weight=1)
        instance.grid(row=index, column=0, sticky="nsew")
