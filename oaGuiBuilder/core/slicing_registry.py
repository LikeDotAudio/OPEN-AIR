import time
import tkinter as tk
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import builder_logger

class BuilderSlicingRegistryMixin:
    """
    Manages the registry of transparent widgets and handles bulk reslicing
    when the background or scroll position changes.
    """

    def register_for_slicing(self, callback):
        """Adds a callback to be executed when the background is updated."""
        if not hasattr(self, '_slicing_registry'):
            self._slicing_registry = []
            
        if callback not in self._slicing_registry:
            if LOCAL_DEBUG: builder_logger.trace(f"👻🔗✨ [ALPHA] Registering widget for transparency slicing in '{getattr(self, 'tab_name', 'Unknown')}'")
            self._slicing_registry.append(callback)
            
            # ⚡ OPTIMIZATION: If background already exists, slice immediately 
            # so the widget doesn't stay 'grey' until the next global event.
            if hasattr(self, 'panel_bg_pil') and self.panel_bg_pil:
                try:
                    # Use root coords if available
                    rx, ry = None, None
                    if hasattr(self, 'scroll_frame') and self.scroll_frame:
                        rx, ry = self.scroll_frame.winfo_rootx(), self.scroll_frame.winfo_rooty()
                    
                    callback(
                        source_bg_pil=self.panel_bg_pil,
                        scroll_ref=self.scroll_frame,
                        scroll_root_x=rx,
                        scroll_root_y=ry
                    )
                except Exception as e:
                    logger.debug(f"Immediate slice failed: {e}")

    def _trigger_reslice_all(self):
        """⚡ BATCH RESLICE ENGINE"""
        if hasattr(self, '_reslice_trigger_id') and self._reslice_trigger_id:
            try:
                self.after_cancel(self._reslice_trigger_id)
            except Exception as e:
                logger.trace(f"Failed to cancel reslice trigger: {e}")
        delay = 150 if getattr(self, '_is_rebuilding', False) else 50
        self._reslice_trigger_id = self.after(delay, self._perform_batch_reslice)

    def _clear_coord_cache(self):
        """Internal optimization: clears cached screen coordinates."""
        self._root_coord_cache = {}

    def _perform_batch_reslice(self):
        """Executes the actual reslice for all widgets using cached shared context."""
        self._reslice_trigger_id = None
        if not self.winfo_exists(): return
        
        # 🛡️ RECURSION GUARD: Prevent infinite background generation loops
        if not hasattr(self, "_bg_regen_count"): self._bg_regen_count = 0
        
        # ⚡ OPTIMIZATION: Clear the coordinate cache once before the batch
        self._clear_coord_cache()

        folds_detected = []
        scroll_ry = 0
        wh = 0
        if hasattr(self, 'scroll_frame') and self.scroll_frame:
            scroll_ry = self.scroll_frame.winfo_rooty()
            wh = self.scroll_frame.winfo_height()
            
            # Search ONLY direct children of the scroll_frame (Top-Level)
            for child in self.scroll_frame.winfo_children():
                is_fold = False
                if hasattr(child, '_oca_path'):
                    path_segments = child._oca_path.split('.')
                    if len(path_segments) == 1 and any('Fold' in s or 'fold' in s for s in path_segments):
                        is_fold = True
                
                if is_fold:
                    try:
                        child_h = child.winfo_height()
                        child_ry = child.winfo_rooty() + (child_h / 2 if child_h > 1 else 0)
                        wy = child_ry - scroll_ry
                        if wh > 0:
                            pos_pct = wy / wh
                            if 0.0 <= pos_pct <= 1.0:
                                folds_detected.append({"position_pct": pos_pct, "orientation": "horizontal"})
                    except Exception as e:
                        logger.trace(f"Failed to calculate fold position for child: {e}")

        folds_detected.sort(key=lambda x: x["position_pct"])

        # Check if we need to regenerate the background for folds
        bg_config = getattr(self, 'config_data', {}).get("background")
        if bg_config and isinstance(bg_config, dict):
            params = bg_config.get("parameters", bg_config)
            fold_params = params.get("metal_fold", {})
            existing_creases = [c for c in fold_params.get("creases", []) if c.get('orientation') == 'horizontal']
            
            needs_update = len(folds_detected) != len(existing_creases)
            if not needs_update and folds_detected:
                for f, e in zip(folds_detected, existing_creases):
                    if abs(f["position_pct"] - float(e["position_pct"])) > 0.005:
                        needs_update = True
                        break
            
            if needs_update:
                if self._bg_regen_count > 3:
                    if LOCAL_DEBUG: builder_logger.warning(f"🛑 [BUILDER] '{getattr(self, 'tab_name', 'Unknown')}': Background regeneration loop detected and suppressed.")
                    self._bg_regen_count = 0
                else:
                    self._bg_regen_count += 1
                    if LOCAL_DEBUG: builder_logger.info(f"📐📏🔄 [BUILDER] '{getattr(self, 'tab_name', 'Unknown')}': Injecting {len(folds_detected)} OcaFold positions into background config.")
                    fold_params["enabled"] = True
                    v_creases = [c for c in fold_params.get("creases", []) if c.get('orientation') == 'vertical']
                    fold_params["creases"] = v_creases + folds_detected
                    params["metal_fold"] = fold_params
                    
                    if hasattr(self, 'scroll_frame') and self.scroll_frame:
                        full_w = max(self.scroll_frame.winfo_width(), self.scroll_frame.winfo_reqwidth())
                        full_h = max(self.scroll_frame.winfo_height(), self.scroll_frame.winfo_reqheight())
                        if hasattr(self, '_apply_panel_background'):
                            self._apply_panel_background(bg_config, full_w, full_h)
                        return
            else:
                self._bg_regen_count = 0
            
        bg_pil = getattr(self, 'panel_bg_pil', None)
        scroll_ref = getattr(self, 'scroll_frame', None)
        
        root_x, root_y = None, None
        if scroll_ref:
            try:
                root_x = scroll_ref.winfo_rootx()
                root_y = scroll_ref.winfo_rooty()
            except Exception as e:
                logger.error(f"🧩🚫🛑 [ERROR] Batch Reslice: Error updating root coords: {e}")

        # If we're still generating a background, defer batch reslice
        if bg_pil is None and getattr(self, '_bg_task_id', 0) > 0:
            if LOCAL_DEBUG: builder_logger.trace(f"🧩⏳🌀 [SYNC] Batch reslice for '{getattr(self, 'tab_name', 'Unknown')}' deferred: Background generation in progress.")
            return

        registry = getattr(self, '_slicing_registry', [])
        if LOCAL_DEBUG: builder_logger.debug(f"🧩🏗️✨ [SYNC] Executing batch reslice for {len(registry)} widgets in '{getattr(self, 'tab_name', 'Unknown')}'")
        
        skipped = 0
        processed = 0
        count = 0
        
        for callback in registry:
            try:
                work_done = callback(
                    source_bg_pil=bg_pil, 
                    scroll_ref=scroll_ref,
                    scroll_root_x=root_x,
                    scroll_root_y=root_y
                )
                if work_done is False: skipped += 1
                else: processed += 1
                count += 1
            except Exception as e:
                logger.error(f"🧩🚫🛑 [ERROR] Batch Reslice: Error in callback: {e}")
        
        if LOCAL_DEBUG:
            builder_logger.info(f"🧩🆗✅ [BUILDER] Reslice COMPLETE: {processed} updated, {skipped} skipped (Jitter Filter) for '{getattr(self, 'tab_name', 'Unknown')}'.")
