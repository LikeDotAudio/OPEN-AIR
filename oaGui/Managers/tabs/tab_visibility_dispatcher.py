# oaGui/Managers/tabs/tab_visibility_dispatcher.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for dispatching visibility events to child widgets within notebook tabs.

def dispatch_tab_visibility_events(notebook_widget, event):
    """Notifies child widgets within tabs when they become visible or hidden."""
    selected_tab_id = notebook_widget.select()

    for tab_id in notebook_widget.tabs():
        tab_frame = notebook_widget.nametowidget(tab_id)
        if not tab_frame.winfo_children():
            continue

        content_widget = tab_frame.winfo_children()[0]
        if tab_id == selected_tab_id:
            if hasattr(content_widget, "_on_gui_visible"):
                content_widget._on_gui_visible(event)
        else:
            if hasattr(content_widget, "_on_gui_hidden"):
                content_widget._on_gui_hidden(event)
