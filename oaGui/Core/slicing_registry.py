# oaGui/Core/slicing_registry.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Orchestrates background-aware transparency slicing for widgets.
# Handles batched reslicing, fold detection, and dynamic background updates.

from oaGui.Constants.builder_constants import (
    SLICING_DELAY_NORMAL,
    SLICING_DELAY_REBUILD,
    SLICING_POSITION_EPSILON,
)
from oaLogging.Methods.matrix_gate import matrix_log


class BuilderSlicingRegistryMixin:
    """
    Registry and synchronization engine for transparent UI components.
    Ensures industrial backgrounds remain pixel-aligned during scrolling or resizing.
    """

    def register_for_slicing(self, callback):
        """Standard API for widgets to subscribe to background update notifications."""
        if not hasattr(self, '_slicing_registry'):
            self._slicing_registry = []

        if callback not in self._slicing_registry:
            self._slicing_registry.append(callback)
            self._trigger_immediate_slice(callback)

    def _trigger_immediate_slice(self, callback):
        """Performs a slice operation for a newly registered widget if the background is ready."""
        if hasattr(self, 'panel_bg_pil') and self.panel_bg_pil:
            try:
                rx, ry = self.scroll_frame.winfo_rootx(), self.scroll_frame.winfo_rooty()
                callback(source_bg_pil=self.panel_bg_pil, scroll_ref=self.scroll_frame,
                         scroll_root_x=rx, scroll_root_y=ry)
            except Exception:
                pass

    def _trigger_reslice_all(self, force=False):
        """Orchestrates a debounced batch reslice for all registered subscribers."""
        if hasattr(self, '_reslice_trigger_id') and self._reslice_trigger_id:
            try: self.after_cancel(self._reslice_trigger_id)
            except Exception: pass

        delay = SLICING_DELAY_REBUILD if getattr(self, '_is_rebuilding', False) else SLICING_DELAY_NORMAL
        self._reslice_trigger_id = self.after(delay, self._perform_batch_reslice)

    def _perform_batch_reslice(self):
        """Top-level batch reslice execution."""
        self._reslice_trigger_id = None
        if not self.winfo_exists(): return

        # 1. Fold Detection and Background Alignment
        self._sync_background_folds()

        # 2. Coordinate Extraction
        bg_pil = getattr(self, 'panel_bg_pil', None)
        scroll_ref = getattr(self, 'scroll_frame', None)
        root_x, root_y = (scroll_ref.winfo_rootx(), scroll_ref.winfo_rooty()) if scroll_ref else (None, None)

        # 3. Notification Dispatch
        registry = getattr(self, '_slicing_registry', [])
        for callback in registry:
            try:
                callback(source_bg_pil=bg_pil, scroll_ref=scroll_ref,
                         scroll_root_x=root_x, scroll_root_y=root_y)
            except Exception as e:
                matrix_log("ui", "gui_builder", "reslice", f"🧩🚫 Callback error: {e}", "TRACE")

    def _sync_background_folds(self):
        """Detects OcaFold widgets and updates the panel background creases."""
        folds = self._detect_visual_folds()
        if not folds: return

        bg_config = getattr(self, 'config_data', {}).get("background")
        if not bg_config or not isinstance(bg_config, dict): return

        if self._folds_require_update(folds, bg_config):
            self._apply_updated_folds(folds, bg_config)

    def _detect_visual_folds(self):
        """Scans children for widgets defining a physical layout fold."""
        folds = []
        if not hasattr(self, 'scroll_frame'): return folds

        s_ry = self.scroll_frame.winfo_rooty()
        wh = self.scroll_frame.winfo_height()
        if wh <= 0: return folds

        for child in self.scroll_frame.winfo_children():
            if self._is_fold_widget(child):
                wy = child.winfo_rooty() + (child.winfo_height() / 2) - s_ry
                folds.append({"position_pct": wy / wh, "orientation": "horizontal"})

        folds.sort(key=lambda x: x["position_pct"])
        return folds

    def _is_fold_widget(self, widget):
        """Heuristic check for fold/separator components."""
        path = getattr(widget, '_oca_path', '')
        return any(s in path for s in ['Fold', 'fold', 'Separator'])

    def _folds_require_update(self, new_folds, bg_config):
        """Determines if the detected folds differ from the current background configuration."""
        fold_params = bg_config.get("parameters", bg_config).get("metal_fold", {})
        existing = [c for c in fold_params.get("creases", []) if c.get('orientation') == 'horizontal']

        if len(new_folds) != len(existing): return True
        for f, e in zip(new_folds, existing):
            if abs(f["position_pct"] - float(e["position_pct"])) > SLICING_POSITION_EPSILON:
                return True
        return False

    def _apply_updated_folds(self, folds, bg_config):
        """Triggers a background regeneration with the new fold positions."""
        params = bg_config.get("parameters", bg_config)
        fold_p = params.get("metal_fold", {})
        fold_p["enabled"] = True

        # Preserve vertical creases
        v_creases = [c for c in fold_p.get("creases", []) if c.get('orientation') == 'vertical']
        fold_p["creases"] = v_creases + folds
        params["metal_fold"] = fold_p

        # Physical Regen
        w = max(self.scroll_frame.winfo_width(), self.scroll_frame.winfo_reqwidth())
        h = max(self.scroll_frame.winfo_height(), self.scroll_frame.winfo_reqheight())
        if hasattr(self, '_apply_panel_background'):
            self._apply_panel_background(bg_config, w, h)
