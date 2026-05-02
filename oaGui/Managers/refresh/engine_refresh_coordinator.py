# Managers/engine_refresh_coordinator.py
# Author: Anthony Peter Kuzub
# Version 20260502.1001.1
#
# Description: Manages the synchronization of background slices using atomic services.

from oaGui.Constants.builder_constants import (
    SLICING_DELAY_NORMAL,
    SLICING_DELAY_REBUILD,
    SLICING_POSITION_EPSILON,
)
from .fold_detector_service import detect_visual_layout_folds
from .batch_slice_dispatcher import dispatch_background_slice_updates

class RefreshCoordinatorMixin:
    """Synchronization engine for transparent UI components via atomic services."""

    def register_for_slicing(self, callback):
        """Standard API for widgets to subscribe to background update notifications."""
        if not hasattr(self, '_slicing_registry'): self._slicing_registry = []
        if callback not in self._slicing_registry:
            self._slicing_registry.append(callback)
            self._trigger_immediate_slice(callback)

    def _trigger_immediate_slice(self, callback):
        """Performs a slice operation for a newly registered widget."""
        if hasattr(self, 'panel_bg_pil') and self.panel_bg_pil:
            try:
                rx, ry = self.scroll_frame.winfo_rootx(), self.scroll_frame.winfo_rooty()
                callback(source_bg_pil=self.panel_bg_pil, scroll_ref=self.scroll_frame, scroll_root_x=rx, scroll_root_y=ry)
            except Exception: pass

    def _trigger_reslice_all(self, force=False):
        """Orchestrates a debounced batch reslice."""
        if hasattr(self, '_reslice_trigger_id') and self._reslice_trigger_id:
            try: self.after_cancel(self._reslice_trigger_id)
            except Exception: pass
        delay = SLICING_DELAY_REBUILD if getattr(self, '_is_rebuilding', False) else SLICING_DELAY_NORMAL
        self._reslice_trigger_id = self.after(delay, self._perform_batch_refresh)

    def _perform_batch_refresh(self):
        """Top-level batch refresh execution via atomic services."""
        self._reslice_trigger_id = None
        if not self.winfo_exists(): return
        self._sync_background_folds()
        dispatch_background_slice_updates(self)

    def _sync_background_folds(self):
        """Detects folds and updates background creases."""
        folds = detect_visual_layout_folds(getattr(self, 'scroll_frame', None))
        if not folds: return

        bg_config = getattr(self, 'configuration', {}).get("background")
        if not bg_config or not isinstance(bg_config, dict): return

        if self._folds_require_update(folds, bg_config):
            self._apply_updated_folds(folds, bg_config)

    def _folds_require_update(self, new_folds, bg_config):
        """Checks if detected folds differ from configuration."""
        fold_params = bg_config.get("parameters", bg_config).get("metal_fold", {})
        existing = [c for c in fold_params.get("creases", []) if c.get('orientation') == 'horizontal']
        if len(new_folds) != len(existing): return True
        for f, e in zip(new_folds, existing):
            if abs(f["position_pct"] - float(e["position_pct"])) > SLICING_POSITION_EPSILON: return True
        return False

    def _apply_updated_folds(self, folds, bg_config):
        """Triggers a background regeneration with new folds."""
        params = bg_config.get("parameters", bg_config)
        fold_p = params.get("metal_fold", {})
        fold_p["enabled"] = True
        v_creases = [c for c in fold_p.get("creases", []) if c.get('orientation') == 'vertical']
        fold_p["creases"] = v_creases + folds
        params["metal_fold"] = fold_p
        w = max(self.scroll_frame.winfo_width(), self.scroll_frame.winfo_reqwidth())
        h = max(self.scroll_frame.winfo_height(), self.scroll_frame.winfo_reqheight())
        if hasattr(self, '_apply_panel_background'): self._apply_panel_background(bg_config, w, h)
