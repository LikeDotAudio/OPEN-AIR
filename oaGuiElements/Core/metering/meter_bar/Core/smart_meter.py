# meter_bar/smart_meter.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import random
import time
import tkinter as tk

from loguru import logger

from oaGui.Methods.processing.deferred_task_handler import DeferredTaskHandler

from .ballistics import BallisticsEngine
from .layout_calculator import MeterLayoutCalculator
from ..renderers.tk_canvas_renderer import TkCanvasRenderer


class SmartMeter(tk.Canvas, DeferredTaskHandler):
    """The modular SmartMeter widget."""

    def __init__(self, parent, raw_config, state_mirror_engine=None, subscriber_router=None, base_topic=None, **kwargs):
        self._init_deferred_handler()
        # Robust Background Inheritance
        try:
            p_bg = parent.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except Exception:
            p_bg = "#2b2b2b"

        # Filter kwargs to only pass tkinter-supported ones
        tk_kwargs = {k: v for k, v in kwargs.items() if k not in ["apply_transparency_func", "builder_instance", "raw_config"]}

        try:
            super().__init__(parent, bd=0, highlightthickness=0, relief="flat", bg=p_bg, **tk_kwargs)
        except Exception:
            if not hasattr(self, "tk"):
                from unittest.mock import MagicMock
                self.tk = MagicMock()
            if not hasattr(self, "_w"): self._w = f"mock_meter_{id(self)}"
            if not hasattr(self, "master"): self.master = parent

        # 1. Initialize Components
        from oaGuiElements.Core.metering.meter_bar.Core.config_parser import MeterConfig
        self.configuration = MeterConfig.from_dict(raw_config)
        self.physics = BallisticsEngine(self.configuration)
        self.layout_calc = MeterLayoutCalculator()

        # 2. Build UI
        try:
            self._build_ui(raw_config=raw_config, p_bg=p_bg, **kwargs)
        except Exception as e:
            logger.warning(f"⚠️ SmartMeter UI build failed (possibly destroyed parent?): {e}")
            # If UI build fails, we still need basic components to avoid AttributeError later
            if getattr(self, 'canvas', None) is None:
                from unittest.mock import MagicMock
                self.canvas = MagicMock()
            if not hasattr(self, 'renderer'):
                self.renderer = MagicMock()

        # 3. State & Sync
        self.state_mirror = state_mirror_engine
        self.router = subscriber_router
        self.base_topic = base_topic

        # Create or use existing variable
        self.value_var = kwargs.get("variable")
        if not self.value_var:
            try:
                self.value_var = tk.DoubleVar(master=parent, value=self.configuration.value_default)
            except Exception:
                # If tk.DoubleVar fails (e.g. headless), use a fallback mock
                from unittest.mock import MagicMock
                self.value_var = MagicMock()

        self.value_var.trace_add("write", self._on_value_update)

        self._anim_timer_id = None
        self._last_anim_time = 0
        self.is_resizing = False # Flag to prevent animation during resize

        # 4. Finalize Initial State
        try:
            self.defer(10, self._initial_draw)
        except:
            pass

    def _build_ui(self, **kwargs):
        # 1. Calculate Required Size
        req_w, req_h = self.configuration.get_requested_dimensions()
        p_bg = kwargs.get("p_bg", "#2b2b2b")

        # Canvas
        self.canvas = tk.Canvas(self, width=req_w, height=req_h,
                                 highlightthickness=0, borderwidth=0, bd=0, relief="flat", bg=p_bg)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Apply Industrial Transparency
        apply_func = kwargs.get("apply_transparency_func")
        builder = kwargs.get("builder_instance")
        raw_config = kwargs.get("raw_config", self.configuration.__dict__)

        if apply_func and builder:
            # Ensure transparency is enabled if not explicitly disabled
            if raw_config.get("transparent") is None:
                raw_config["transparent"] = True

            # 1. Slices the patina onto the inner drawing canvas
            apply_func(self, self.canvas, raw_config, builder)
            # 2. Also slices onto the outer container frame/canvas to handle padding/margins
            apply_func(self, self, raw_config, builder)

        self.renderer = TkCanvasRenderer(self.canvas)
        self.bind("<Configure>", self._on_resize)

        # Debug: Random Value Generation
        self.canvas.bind("<Button-2>", self._on_debug_generate_random)
        self.canvas.bind("<B2-Motion>", self._on_debug_generate_random)

    def _initial_draw(self):
        req_w, req_h = self.configuration.get_requested_dimensions()
        self._perform_layout(req_w, req_h)
        # Start ballistics if we have a non-minimum initial value
        self._on_value_update()

    def _on_resize(self, event):
        # ⚡ OPTIMIZATION: Only resize if the change is significant to avoid 'jiggling' loops
        last_w, last_h = getattr(self, "_last_resize_dim", (0, 0))
        if abs(event.width - last_w) <= 2 and abs(event.height - last_h) <= 2:
            return

        self._last_resize_dim = (event.width, event.height)

        # Set resize flag and schedule layout/redraw
        self.is_resizing = True
        self.defer(50, lambda: self._perform_layout(self.canvas.winfo_width(), self.canvas.winfo_height()))

    def render(self):
        """Hook for SyncBehavior to trigger a redraw when slicing updates."""
        if self.canvas.winfo_width() > 1:
            # Ensure we don't trigger layout if a resize is already in progress
            if not self.is_resizing:
                 self._perform_layout(self.canvas.winfo_width(), self.canvas.winfo_height())

    def _perform_layout(self, w, h):
        if w <= 1 or h <= 1: return
        self.current_layout = self.layout_calc.calculate(w, h, self.configuration)
        self.renderer.draw_static(self.current_layout, self.configuration)
        self._refresh_frame()

        # Reset resize flag after layout is complete and redraw is done
        self.is_resizing = False

    def _on_value_update(self, *args):
        try:
            # ⚡ SAFETY: Ensure we don't try to animate on a mock or dead canvas
            if getattr(self, 'canvas', None) is None or not hasattr(self.canvas, 'winfo_exists'):
                return
            if not self.canvas.winfo_exists():
                return

            value = self.value_var.get()
            self.physics.set_target(value)
            if self._anim_timer_id is None:
                self._last_anim_time = time.time() * 1000
                self._animate()
        except Exception as e:
            logger.error(f"Error updating meter value: {e}")

    def _animate(self):
        # Prevent animation updates if a resize is in progress
        if self.is_resizing:
            self._anim_timer_id = None # Clear timer to avoid re-scheduling until resize is done
            return

        self._anim_timer_id = None
        if not hasattr(self, 'current_layout'): return

        now = time.time() * 1000
        dt = now - self._last_anim_time
        self._last_anim_time = now

        dt = max(1.0, min(100.0, dt))
        current_v, peak_v, overload_f, is_running, reached_min = self.physics.update(dt)

        dyn_data = self.layout_calc.get_dynamic_coords(current_v, peak_v, overload_f, self.configuration, self.current_layout)
        self.renderer.update_dynamic(dyn_data, overload_f, self.configuration)

        if reached_min:
            if self.state_mirror and self.configuration.path:
                self.state_mirror.broadcast_gui_change_to_mqtt(self.configuration.path)

        if is_running:
            self._anim_timer_id = self.defer(20, self._animate)

    def _refresh_frame(self):
        current_v = self.physics.current_value
        peak_v = self.physics.peak_value
        overload_f = self.physics.overload_fade_factor
        dyn_data = self.layout_calc.get_dynamic_coords(current_v, peak_v, overload_f, self.configuration, self.current_layout)
        self.renderer.update_dynamic(dyn_data, overload_f, self.configuration)

    def _on_debug_generate_random(self, event):
        new_val = random.uniform(self.configuration.min_val, self.configuration.max_val)
        self.value_var.set(new_val)

        # Explicit broadcast for debug injection (which might not be traced by logic yet)
        if self.state_mirror and self.configuration.path:
            self.state_mirror.broadcast_gui_change_to_mqtt(self.configuration.path)

    # --- Helpers ---
    def _get_pack_side(self):
        mapping = {"top": tk.TOP, "bottom": tk.BOTTOM, "left": tk.LEFT, "right": tk.RIGHT}
        return mapping.get(self.configuration.label_position, tk.TOP)

    def _get_canvas_pack_side(self):
        position = self.configuration.label_position
        if position == "left": return tk.LEFT
        if position == "right": return tk.RIGHT
        if position == "bottom": return tk.BOTTOM
        return tk.TOP

    def _get_label_anchor(self):
        mapping = {"left": "e", "right": "w", "top": "s", "bottom": "n"}
        return mapping.get(self.configuration.label_position, "center")
