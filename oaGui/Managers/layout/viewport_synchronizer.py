# oaGui/Managers/layout/viewport_synchronizer.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Synchronizes the physical canvas and content dimensions with the current viewport.

def synchronize_viewport_dimensions(layout_manager, width, height):
    """Calculates and applies new dimensions to the canvas and inner frame."""
    layout_manager._resize_timer = None

    if width <= 1 or height <= 1:
        return

    if not hasattr(layout_manager.builder, 'viewport_manager') or \
       not layout_manager.builder.viewport_manager:
        return

    result = layout_manager.builder.viewport_manager.synchronize_to_viewport(width, height)
    if not result:
        return

    # Notify footer of updated dimensions
    if hasattr(layout_manager.builder, 'footer') and layout_manager.builder.footer:
        layout_manager.builder.footer.update_dimensions(
            width, height,
            result["content"][0], result["content"][1]
        )

    # Sync background patina
    if hasattr(layout_manager.builder, '_trigger_background_sync'):
        layout_manager.builder._trigger_background_sync(force=True)
