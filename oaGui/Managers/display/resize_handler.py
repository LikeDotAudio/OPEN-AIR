# oaGui/Managers/display/resize_handler.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Manages debounced global resize events for the application.

def handle_global_resize(display_instance, event):
    """Orchestrates the debounced resize lifecycle."""
    if event.widget != display_instance.root:
        return

    display_instance.global_resizing = True
    
    if hasattr(display_instance, '_resize_timer') and display_instance._resize_timer:
        display_instance.after_cancel(display_instance._resize_timer)
    
    display_instance._resize_timer = display_instance.after(
        200, 
        lambda: _complete_resize_sequence(display_instance)
    )

def _complete_resize_sequence(display_instance):
    """Finalizes the resize event and notifies observers."""
    display_instance._resize_timer = None
    display_instance.global_resizing = False
    try: 
        display_instance.event_generate("<<GlobalResizeDone>>")
    except: 
        pass
