# Interface/Window/editor_toolbar.py
# Author: Gemini CLI
# Version: 20260417.0100.1
#
# Description: Global toolbar for the WYSIWYG Editor.

import tkinter as tk
from oaComBroker.Core.event_bus import event_bus

class EditorToolbar(tk.Frame):
    """Top-level toolbar for quick actions and bespoke editor launching."""
    
    def __init__(self, parent, editor):
        super().__init__(parent, bg="#333333", height=38)
        self.editor = editor
        self.pack_propagate(False)
        
        # --- Left Section: Contextual Tools ---
        self.context_frame = tk.Frame(self, bg="#333333")
        self.context_frame.pack(side="left", fill="y", padx=5)

        self.bespoke_btn = tk.Button(
            self.context_frame, 
            text="Launch element editor", 
            bg="#33A1FD", 
            fg="white", 
            font=("Arial", 8, "bold"), 
            relief="flat", 
            padx=12,
            pady=2,
            activebackground="#4db3ff",
            activeforeground="white",
            command=self._launch_bespoke
        )
        # Initially hidden
        self.bespoke_btn.pack_forget()

        # --- Right Section: Global Actions ---
        self.action_frame = tk.Frame(self, bg="#333333")
        self.action_frame.pack(side="right", fill="y", padx=5)

        tk.Button(
            self.action_frame,
            text="REBUILD",
            bg="#444444",
            fg="#00FF00",
            font=("Arial", 8, "bold"),
            relief="flat",
            padx=10,
            command=lambda: self.editor.layout_view._manual_rebuild() if hasattr(self.editor, 'layout_view') else None
        ).pack(side="right", padx=5, pady=5)

        # Subscribe to focus events to show/hide the bespoke button
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)

    def _on_focus_requested(self, path, source=None):
        """Update toolbar state based on the selected element."""
        # Wait a small bit for ElementProperties to update its refresh_mgr
        self.after(50, self._check_bespoke_availability)

    def _check_bespoke_availability(self):
        if not self.winfo_exists(): return
        
        show = False
        if hasattr(self.editor, 'props_tab') and hasattr(self.editor.props_tab, 'refresh_mgr'):
            if self.editor.props_tab.refresh_mgr.bespoke_editor_info:
                show = True
        
        if show:
            self.bespoke_btn.pack(side="left", padx=5, pady=5)
        else:
            self.bespoke_btn.pack_forget()

    def _launch_bespoke(self):
        if hasattr(self.editor, 'props_tab'):
            self.editor.props_tab.launch_bespoke_editor()
