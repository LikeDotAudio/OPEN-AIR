# oaGui/Managers/refresh/fold_detector_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for detecting physical layout folds in the UI hierarchy.

def detect_visual_layout_folds(scroll_frame):
    """
    Scans child widgets for components defining a physical layout fold/separator.
    Returns a sorted list of fold metadata (position_pct, orientation).
    """
    folds = []
    if not scroll_frame or not scroll_frame.winfo_exists():
        return folds

    scroll_root_y = scroll_frame.winfo_rooty()
    view_height = scroll_frame.winfo_height()

    if view_height <= 0:
        return folds

    for child in scroll_frame.winfo_children():
        path = getattr(child, '_oca_path', '')
        if any(s in path for s in ['Fold', 'fold', 'Separator']):
            # Calculate midpoint relative to scrollable area
            mid_y = child.winfo_rooty() + (child.winfo_height() / 2) - scroll_root_y
            folds.append({
                "position_pct": mid_y / view_height,
                "orientation": "horizontal"
            })

    # Ensure deterministic order
    folds.sort(key=lambda x: x["position_pct"])
    return folds
