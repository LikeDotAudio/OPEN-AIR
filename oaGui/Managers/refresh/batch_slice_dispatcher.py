# oaGui/Managers/refresh/batch_slice_dispatcher.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for dispatching background slice updates to registered callbacks.

from oaLogging.Methods.matrix_gate import matrix_log


def dispatch_background_slice_updates(refresh_instance):
    """Notifies all registered subscribers that a new background slice is ready."""
    bg_pil = getattr(refresh_instance, 'panel_bg_pil', None)
    scroll_frame = getattr(refresh_instance, 'scroll_frame', None)

    if not scroll_frame or not scroll_frame.winfo_exists():
        return

    root_x, root_y = scroll_frame.winfo_rootx(), scroll_frame.winfo_rooty()
    registry = getattr(refresh_instance, '_slicing_registry', [])

    for callback in registry:
        try:
            callback(
                source_bg_pil=bg_pil,
                scroll_ref=scroll_frame,
                scroll_root_x=root_x,
                scroll_root_y=root_y
            )
        except Exception as error:
            matrix_log("ui", "refresh", "dispatch", f"🧩🚫 Dispatch error: {error}", "TRACE")
