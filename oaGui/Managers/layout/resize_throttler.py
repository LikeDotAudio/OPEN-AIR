# oaGui/Managers/layout/resize_throttler.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Throttles physical resize events to prevent excessive layout recalculations.

from oaGui.Constants.builder_constants import RESIZE_THROTTLE_DELAY, RESIZE_WIDTH_THRESHOLD

def throttle_resize_event(layout_manager, event):
    """Throttles configure events using a distance threshold and time-based delay."""
    if event.widget != layout_manager.builder:
        return
    if getattr(layout_manager.builder, '_is_rebuilding', False):
        return

    width, height = event.width, event.height

    # Only react if the change exceeds the threshold
    if abs(width - layout_manager._last_w) < RESIZE_WIDTH_THRESHOLD and \
       abs(height - layout_manager._last_h) < RESIZE_WIDTH_THRESHOLD:
        return

    layout_manager._last_w = width
    layout_manager._last_h = height

    if layout_manager._resize_timer:
        layout_manager.builder.after_cancel(layout_manager._resize_timer)
    
    layout_manager._resize_timer = layout_manager.builder.after(
        RESIZE_THROTTLE_DELAY, 
        layout_manager.trigger_final_resize
    )
    
    _trigger_editor_grid_refresh(layout_manager)

def _trigger_editor_grid_refresh(layout_manager):
    """Optional refresh for the WYSIWYG design grid."""
    if getattr(layout_manager.builder, 'is_editor', False):
        from oaGuiEditorWYSIWYG.Methods.builder_editor_grid import BuilderEditorGrid
        layout_manager.builder.after(
            RESIZE_THROTTLE_DELAY + 10, 
            lambda: BuilderEditorGrid.draw(
                layout_manager.builder.canvas, 
                layout_manager.builder.scroll_frame, 
                True
            )
        )
