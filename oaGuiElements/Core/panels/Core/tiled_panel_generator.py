# panels/tiled_panel_generator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect
import math
import random

from PIL import Image

from oaLogging.Methods.matrix_gate import matrix_log
from oaStateCache.Core.work_stealing_pool import WorkStealingPool

from oaGuiElements.Constants.gui_constants import DEFAULT_PANEL_CONFIG
from .panel_generator import PanelGenerator

# ⚡ PERSISTENCE: The pool lives for the duration of the application.
_GLOBAL_STEALING_POOL = None

class TiledPanelGenerator:
    """
    Experimental Work-Stealing Generator.
    Divides the panel into tiles and processes them across a work-stealing pool.
    """

    @staticmethod
    def _get_pool():
        global _GLOBAL_STEALING_POOL
        if _GLOBAL_STEALING_POOL is None:
            import multiprocessing
            cores = multiprocessing.cpu_count()
            _GLOBAL_STEALING_POOL = WorkStealingPool(num_workers=max(2, cores - 1))
        return _GLOBAL_STEALING_POOL

    @staticmethod
    def generate_tiled(width, height, config=None, tile_size=256):
        """
        Main entry point for tiled generation. 
        """
        if not config or not isinstance(config, dict):
            config = DEFAULT_PANEL_CONFIG

        pool = TiledPanelGenerator._get_pool()

        # Calculate grid
        cols = math.ceil(width / tile_size)
        rows = math.ceil(height / tile_size)

        tasks = []

        # ⚡ TASK SEEDING: We must pass the SAME seed to every tile task
        # so that global patterns (like streaks) align correctly.
        params = config.get("parameters", config)
        base_seed = params.get("random_seed", random.randint(1, 1000000))

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🧩🏗️🌀 [STEALING] Processing {cols*rows} tiles ({width}x{height}) via Work-Stealing Pool.", level="INFO")
        start_time = math.perf_counter()

        for r in range(rows):
            for c in range(cols):
                # Calculate tile bounds
                x1 = c * tile_size
                y1 = r * tile_size
                tw = min(tile_size, width - x1)
                th = min(tile_size, height - y1)

                # We define a task as (function, args, kwargs)
                # For this proof of concept, we use the existing PanelGenerator
                # but we will need to evolve it to support 'global offsets'.
                tasks.append((
                    TiledPanelGenerator._process_single_tile,
                    (tw, th, x1, y1, width, height, base_seed, config),
                    {}
                ))

        # ⚡ STEAL TIME: Dispatch the batch to the pool
        results = pool.apply_batch(tasks)

        # Stitching
        final_img = Image.new("RGBA", (width, height), (43, 43, 43, 255))
        for tile_img, x, y in results:
            final_img.paste(tile_img, (x, y))

        end_time = math.perf_counter()
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🧩🆗✨ [STEALING] Tiled render complete in {(end_time - start_time)*1000:.2f}ms.", level="SUCCESS")

        return final_img

    @staticmethod
    def _process_single_tile(tw, th, x_off, y_off, total_w, total_h, seed, config):
        """
        Worker function: Generates a single tile of the patina.
        """
        # Set the seed for this worker thread
        random.seed(seed)

        # ⚡ SEAMLESS LOGIC (Future implementation):
        # We would pass x_off/y_off to the layers so they sample the noise
        # at the correct global coordinates.
        # For now, we simulate by generating the whole thing and cropping,
        # which isn't efficient but proves the work-stealing flow.

        # ⚡ OPTIMIZATION: Sampling logic should be moved into PanelGenerator to avoid
        # generating full-resolution buffers for single tile crops.
        full_panel = PanelGenerator.generate_procedural_panel(total_w, total_h, config)
        tile = full_panel.crop((x_off, y_off, x_off + tw, y_off + th))

        return (tile, x_off, y_off)
